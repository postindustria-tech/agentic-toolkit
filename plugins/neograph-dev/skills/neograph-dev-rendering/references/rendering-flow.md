# Rendering Data Flow

Step-by-step trace of how a Pydantic model becomes text in the LLM prompt,
for both prompt types.

## Template-Ref Prompt Flow

Example: `Node("proc", prompt="rw/summarize", inputs={"seed": Claims})`

```
1. factory._extract_input(state, node)
   -> InputShape.FAN_IN_DICT
   -> {"seed": Claims(items=["a", "b"])}

2. _dispatch.ThinkDispatch.execute()
   -> rendered = _render_input(node, input_data)

3. _dispatch._render_input(node, input_data)
   -> prompt is "rw/summarize" (no space, no ${)
   -> NOT inline, proceed to render
   -> effective_renderer = node.renderer or _get_global_renderer()
   -> render_input(input_data, renderer=effective_renderer)

4. renderers.render_input({"seed": Claims(...)}, renderer=None)
   -> isinstance(input_data, dict) -> True
   -> {k: _render_single(v, None) for k, v in items()}

5. renderers._render_single(Claims(...), renderer=None)
   -> no render_for_prompt() on Claims
   -> renderer is None
   -> isinstance(value, BaseModel) -> True
   -> describe_value(Claims(items=["a", "b"]))
   -> "{\n  items: [\n    \"a\"\n    \"b\"\n  ]\n}"

6. rendered = {"seed": "{\n  items: [...]\n}"}

7. invoke_structured(input_data=rendered, ...)
   -> _compile_prompt("rw/summarize", rendered, ...)
   -> NOT inline, delegates to prompt_compiler
   -> prompt_compiler("rw/summarize", {"seed": "<BAML string>"}, ...)
```

## Inline Prompt Flow

Example: `Node("proc", prompt="Summarize: ${seed.items}", inputs={"seed": Claims})`

```
1. factory._extract_input(state, node)
   -> {"seed": Claims(items=["a", "b"])}

2. _dispatch.ThinkDispatch.execute()
   -> rendered = _render_input(node, input_data)

3. _dispatch._render_input(node, input_data)
   -> prompt is "Summarize: ${seed.items}"
   -> _is_inline_prompt("Summarize: ${seed.items}") -> True (has space)
   -> return input_data UNCHANGED (raw models)

4. invoke_structured(input_data={"seed": Claims(...)}, ...)
   -> _compile_prompt("Summarize: ${seed.items}", {"seed": Claims(...)}, ...)
   -> _is_inline_prompt -> True
   -> _substitute_vars(template, input_data)

5. _resolve_var("seed.items", {"seed": Claims(items=["a", "b"])})
   -> parts = ["seed", "items"]
   -> root = input_data["seed"] = Claims(items=["a", "b"])  # RAW model
   -> rest = ["items"]
   -> obj = getattr(Claims(...), "items") = ["a", "b"]
   -> NOT a BaseModel -> str(["a", "b"]) = "['a', 'b']"

6. Result: "Summarize: ['a', 'b']"
   -> returned as [{"role": "user", "content": "Summarize: ['a', 'b']"}]
```

## render_for_prompt() Flow

Example: model with `render_for_prompt()` returning a projected BaseModel.

```
1. _render_single(FullData(raw="hello", internal_id=42), renderer=None)

2. hasattr(FullData, "render_for_prompt") -> True
   -> result = FullData.render_for_prompt()
   -> result = Presentation(summary="HELLO", score=0.95)

3. isinstance(result, str) -> False
   isinstance(result, BaseModel) -> True
   renderer is None -> True
   -> describe_value(Presentation(summary="HELLO", score=0.95))

4. Output: "{\n  summary: \"HELLO\"\n  score: 0.95\n}"
   (internal_id is NOT in the output — projection stripped it)
```

## Tool Result Flow (for parity comparison)

```
1. _render_tool_result_for_llm(Claims(items=["a"]), renderer=None)

2. isinstance(result, BaseModel) -> True
   renderer is None -> True
   -> describe_value(Claims(items=["a"]), prefix="Tool result:")

3. Output: "Tool result:\n{\n  items: [\n    \"a\"\n  ]\n}"
```

The BAML body is identical to the input rendering path — only the prefix differs.
