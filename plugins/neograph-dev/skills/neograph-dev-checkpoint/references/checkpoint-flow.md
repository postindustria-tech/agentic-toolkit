# Checkpoint Data Flow

Step-by-step trace of how schema fingerprinting and auto-resume work.

## Compile-Time Flow

```
compile(construct, checkpointer=MemorySaver())

1. state.compile_state_model(construct)
   -> state_model: type[BaseModel]  (one field per node output + framework fields)

2. state.compute_schema_fingerprint(state_model)
   -> exclude neo_*, node_id, project_root, human_feedback
   -> sort (field_name, str(annotation)) pairs
   -> sha256(repr(sorted_items))[:16]
   -> e.g. "a3f1c8e90d2b4567"

3. state.compute_node_fingerprints(construct)
   -> for each node:
      -> hash_input = f"{field_name}:{output_type.__qualname__}"
      -> sha256(hash_input)[:12]
   -> {"prepare": "a1b2c3d4e5f6", "enrich": "f6e5d4c3b2a1", ...}

4. compiler.py:204-205
   -> compiled._neo_schema_fingerprint = "a3f1c8e90d2b4567"
   -> compiled._neo_node_fingerprints = {"prepare": "...", "enrich": "...", ...}
```

## First Run Flow

```
run(graph, input={"node_id": "BR-001"}, config={"configurable": {"thread_id": "t1"}})

1. runner.py:267-272 -- inject fingerprints into input
   -> input["neo_schema_fingerprint"] = "a3f1c8e90d2b4567"
   -> input["neo_node_fingerprints"] = {"prepare": "...", ...}

2. _has_existing_checkpoint(graph, config) -> False (first run)

3. graph.invoke(input, config=config)
   -> executes all nodes: prepare -> enrich -> analyze -> report
   -> checkpoint stores: node outputs + neo_schema_fingerprint + neo_node_fingerprints
```

## Resume With Schema Change

```
# User changes analyze's output type (e.g., AnalysisV1 -> AnalysisV2)
graph_v2 = compile(pipeline_v2, checkpointer=checkpointer)
# graph_v2._neo_node_fingerprints["analyze"] is now different

run(graph_v2, input={"node_id": "BR-001"}, config={"configurable": {"thread_id": "t1"}})

1. _has_existing_checkpoint(graph_v2, config) -> True

2. _verify_checkpoint_schema(graph_v2, config, auto_resume=True)

3. Read stored fingerprint from checkpoint:
   -> state = graph_v2.get_state(config)
   -> stored_fp = state.values["neo_schema_fingerprint"]  # old fingerprint
   -> current_fp = graph_v2._neo_schema_fingerprint         # new fingerprint
   -> stored_fp != current_fp  (mismatch!)

4. _compute_invalidated_nodes(graph_v2, state.values)
   -> current_nfp = graph_v2._neo_node_fingerprints
   -> stored_nfp = state.values["neo_node_fingerprints"]
   -> compare each node:
      - prepare: same -> skip
      - enrich:  same -> skip
      - analyze: DIFFERENT -> changed.add("analyze")
      - report:  same -> skip
   -> return {"analyze"}

5. _auto_resume_from_divergence(graph_v2, config, {"analyze"})
   -> walk get_state_history(config):
      Snapshot 5: next=() [final]          -> skip
      Snapshot 4: next=("report",)         -> "report" not in {"analyze"} -> skip
      Snapshot 3: next=("analyze",)        -> "analyze" IN {"analyze"} -> MATCH!
      -> rewind_checkpoint_id = snapshot_3.config["configurable"]["checkpoint_id"]
      -> config["configurable"]["checkpoint_id"] = rewind_checkpoint_id

6. Back in run():
   -> graph_v2.invoke(None, config=config)
   -> LangGraph sees checkpoint_id pointing to snapshot 3
   -> Resumes from there: executes analyze (with new type) then report
   -> prepare and enrich outputs preserved from checkpoint
```

## Strict Mode Flow (auto_resume=False)

```
run(graph_v2, input={"node_id": "BR-001"}, config=config, auto_resume=False)

1-4. Same as above (detect mismatch, compute invalidated nodes)

5. auto_resume=False
   -> raise CheckpointSchemaError(
        f"Checkpoint fingerprint {stored_fp} != current {current_fp}",
        invalidated_nodes={"analyze"}
      )

6. Caller catches:
   try:
       run(graph_v2, ..., auto_resume=False)
   except CheckpointSchemaError as e:
       print(e.invalidated_nodes)  # {"analyze"}
       # decide: delete checkpoint, migrate, or handle
```
