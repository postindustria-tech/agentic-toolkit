---
name: neograph-dev-checkpoint
description: >
  This skill should be used when the user asks about "checkpoint", "auto_resume",
  "schema fingerprint", "CheckpointSchemaError", "time-travel", "rewind",
  "per-node invalidation", "checkpoint resume", or needs to understand how
  neograph detects schema changes and re-executes affected nodes.
version: 0.1.0
---

# Neograph Checkpoint System

Schema-aware checkpoint resume that automatically detects what changed and
re-executes only affected nodes. Based on the Prefect cache-miss model.

## Schema Fingerprinting

Two fingerprint functions in `state.py`:

### compute_schema_fingerprint(state_model) -- state.py:298
SHA-256 prefix (16 chars) of sorted `(field_name, annotation_string)` pairs.
Excludes framework fields (`neo_*`, `node_id`, `project_root`, `human_feedback`).
Changes when any field is added/removed or its type changes.

### compute_node_fingerprints(construct) -- state.py:262
`dict[str, str]` mapping each node's state field name to a SHA-256 prefix (12 chars).
Hash input: `"{field_name}:{type.__qualname__}"`.
For dict-form outputs (multi-output): one fingerprint per output key.
For sub-constructs: fingerprinted by their `output` type.

## Compile-Time Attachment

`compiler.py:204-205` stashes both fingerprints on the compiled graph:
```python
compiled._neo_schema_fingerprint = compute_schema_fingerprint(state_model)
compiled._neo_node_fingerprints = compute_node_fingerprints(construct)
```

## Run-Time Injection

`runner.py:267-272` injects fingerprints into the initial state dict so they
persist in the checkpoint alongside node outputs.

## Resume Flow

`_verify_checkpoint_schema()` in `runner.py:74-127`:

1. Read stored `neo_schema_fingerprint` from checkpoint channel_values
2. Compare against current `_neo_schema_fingerprint` on the compiled graph
3. If match: resume normally
4. If mismatch:
   - `_compute_invalidated_nodes()` diffs per-node fingerprints
   - `auto_resume=True`: call `_auto_resume_from_divergence()`
   - `auto_resume=False`: raise `CheckpointSchemaError(invalidated_nodes=...)`

## Auto-Resume: The LangGraph Time-Travel Pattern

`_auto_resume_from_divergence()` in `runner.py:129-154`:

1. Walk `graph.get_state_history(config)` backwards (newest to oldest)
2. Find the snapshot where an invalidated node appears in `.next`
   (meaning "this checkpoint was taken just before that node ran")
3. Extract `checkpoint_id` from that snapshot's config
4. Mutate caller's `config["configurable"]["checkpoint_id"]` in-place
5. Back in `run()`, `graph.invoke(None, config=config)` resumes from rewind point
6. LangGraph naturally re-executes from the rewind point forward

The key insight: by rewinding to before the earliest changed node, all
downstream nodes are automatically re-executed by LangGraph's normal
execution flow. No transitive dependency tracking needed.

## CheckpointSchemaError

`errors.py:143`. Raised when `auto_resume=False` and fingerprints mismatch.

```python
class CheckpointSchemaError(NeographError):
    invalidated_nodes: set[str]  # which state fields changed
```

## What Triggers Invalidation

| Change | Detected? |
|--------|-----------|
| Output class renamed | Yes |
| Field added to output | Yes |
| Field removed | Yes |
| Field type changed | Yes |
| Node added (new, not in stored) | No (skipped) |
| Prompt text changed | No (type-based) |
| Logic changed (same types) | No |

## When to Use auto_resume=False

- CI/production where you want explicit control over schema migrations
- When you need to inspect `invalidated_nodes` before deciding to proceed
- When checkpoint data is expensive to regenerate and you want manual review

## Gates

Before modifying checkpoint code:

- [ ] Fingerprint computation is deterministic (same inputs -> same hash)
- [ ] Framework fields excluded from fingerprint
- [ ] Pre-fingerprint checkpoints (no stored fingerprint) resume normally
- [ ] New nodes (absent from stored fingerprints) don't trigger invalidation
- [ ] auto_resume=True rewinds to correct checkpoint (before earliest changed node)
- [ ] auto_resume=False raises CheckpointSchemaError with correct invalidated_nodes
- [ ] Config mutation is in-place (caller's dict modified)

## Anti-Patterns

- **Comparing fingerprints without checking for pre-fingerprint checkpoints.**
  Old checkpoints have no stored fingerprint. Treat missing as "compatible" (fail open).
- **Transitive invalidation via DAG walking.** Not needed -- rewinding to before the
  earliest changed node naturally causes LangGraph to re-execute everything downstream.
- **Using auto_resume with non-persistent checkpointers in production.** MemorySaver
  loses data on process restart. Use SqliteSaver or PostgresSaver for durable checkpoints.

## Additional Resources

### Reference Files

- **`references/checkpoint-flow.md`** - Step-by-step data flow for the checkpoint system
