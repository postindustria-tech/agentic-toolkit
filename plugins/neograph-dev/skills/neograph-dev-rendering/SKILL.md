---
name: neograph-dev-rendering
description: >
  This skill should be used when the user asks about "rendering", "BAML",
  "describe_value", "render_input", "render_for_prompt", "prompt input
  rendering", "tool result rendering", "inline prompt", "template-ref prompt",
  "${var} resolution", or when working on code that touches how Pydantic models
  are converted to text for LLM consumption.
version: 0.1.0
---

# Neograph Rendering Dispatch

Provides the complete rendering architecture: how Pydantic models become text
for LLMs, the dispatch hierarchy, inline vs template-ref prompt distinction,
and the BAML default rendering behavior.

## The Two Prompt Systems

Neograph has two fundamentally different prompt resolution paths. Mixing them
up is the #1 source of rendering bugs.

### Inline Prompts (`${var}` syntax)

Detected by: contains a space OR contains `${`.
Resolved by: `_substitute_vars()` in `_llm.py`.

```python
Node("proc", prompt="Summarize: ${seed.text}", ...)
```

- Neograph resolves `${var}` and `${var.field}` internally
- Consumer's `prompt_compiler` is NEVER called
- Input data must be **raw** (not BAML-rendered) for dotted access
- `_render_input` in `_dispatch.py` skips rendering for inline prompts

### Template-Ref Prompts (bare name)

Detected by: no space AND no `${`.
Resolved by: consumer's `prompt_compiler` callback.

```python
Node("proc", prompt="rw/summarize", ...)
```

- Neograph passes the name + rendered input_data to `prompt_compiler`
- Input data is **BAML-rendered** before reaching the prompt_compiler
- Consumer does `template.format(**data)` or equivalent
- Placeholder format is `{var}` (Python str.format), NOT `${var}`

## Rendering Dispatch Hierarchy

For each Pydantic value flowing into a prompt:

1. **`render_for_prompt()` method** wins if defined on the model (always
   checked, regardless of renderer config)
2. **Explicit renderer** (XmlRenderer / DelimitedRenderer / JsonRenderer)
   if configured via `node.renderer` or `configure_llm(renderer=...)`
3. **BAML default** via `describe_value()` — the fallback when no renderer
   is configured. Symmetric with tool-result rendering.
4. **Primitives** pass through unchanged (str, int, etc.)

### RenderedInput dataclass
`renderers.py:32`. The single object that bundles all rendering artifacts:
- `raw` -- original Pydantic models for inline `${var}` dotted access
- `rendered` -- BAML strings for template-ref prompts
- `flattened` -- extra fields from `render_for_prompt()` BaseModel returns (template-ref only)
- `available_keys_inline` -- keys valid for inline prompts (raw dict keys only)
- `available_keys_template` -- keys valid for template-ref prompts (raw + flattened + extras)
- `for_template_ref` property -- merges `rendered` + `flattened`

Produced by `build_rendered_input(input_data, renderer=None)`.

### Field flattening (render_for_prompt BaseModel returns)
When `render_for_prompt()` returns a BaseModel, `_render_with_flattening()` (renderers.py:320) iterates each field:
- BaseModel children and list[BaseModel] children are **preserved as objects** (not string-rendered) for dotted template access
- Other values are rendered via `_render_single`
- The whole returned model is also rendered as a single string

These fields become individually addressable template vars in template-ref prompts (via `RenderedInput.flattened`).

Lint-time: `_get_flattened_field_names()` in lint.py:309 predicts flattened keys from return type annotations without calling the method.

### list[BaseModel] handling
In `_render_single()` (renderers.py:384-386): non-empty `list[BaseModel]` gets BAML-rendered via `describe_value()`, same as single models.
In `_render_with_flattening()` (renderers.py:342-343): `list[BaseModel]` children are preserved as objects in flattened dict for indexed template access.

### ExcludeFromOutput marker
`describe_type.py:18`. Annotated marker for Pydantic fields. Fields with this marker:
- Visible in input rendering (describe_value, XmlRenderer, etc.)
- Excluded from describe_type() output schema (LLM won't produce them)
- Must have a default value

### Where rendering happens

| Prompt type | Rendering location | Input to next stage |
|-------------|-------------------|-------------------|
| Template-ref | `_dispatch.py:_render_input` | BAML strings in dict |
| Inline | Skipped in `_render_input` | Raw models in dict |

For template-ref: `ThinkDispatch.execute()` calls `_render_input(node, input_data)`,
which calls `render_input(data, renderer=effective_renderer)` in `renderers.py`.
The rendered dict then flows to `invoke_structured()` -> `_compile_prompt()` ->
consumer's `prompt_compiler`.

For inline: `_render_input` detects `_is_inline_prompt(node.prompt)` and returns
raw data unchanged. `_compile_prompt()` calls `_substitute_vars()` which does
raw attribute access. At the leaf, `_resolve_var` calls `describe_value()` on
BaseModel values instead of `str()`.

## The Parity Invariant

Tool-result rendering and prompt-input rendering produce identical BAML for the
same Pydantic instance under default config. Both use `describe_value()`.

```python
from neograph._llm import _render_tool_result_for_llm
from neograph.renderers import render_input
from neograph.describe_type import describe_value

# These produce the same BAML body:
tool_output = _render_tool_result_for_llm(instance, renderer=None)
input_output = render_input(instance, renderer=None)
direct = describe_value(instance)

assert input_output == direct
```

## Gates

Before modifying rendering code:

- [ ] Parity invariant holds (tool-result == input BAML for same model)
- [ ] `render_for_prompt()` fires regardless of renderer config
- [ ] Inline prompts get raw data (dotted access works)
- [ ] Template-ref prompts get rendered data
- [ ] `Field(exclude=True)` honored in BAML output
- [ ] `ExcludeFromOutput` marker honored in BAML schema but visible in input rendering
- [ ] Tests through full dispatch chain (not just `render_input` directly)
- [ ] RenderedInput fields correctly populated for both prompt types
- [ ] Field flattening preserves BaseModel children as objects
- [ ] list[BaseModel] rendered via describe_value, not str()

## Anti-Patterns

- **Rendering before var substitution for inline prompts.** `_render_input`
  must skip rendering when the prompt is inline, otherwise `${claim.text}`
  does `getattr(baml_string, "text")` and returns empty string.
- **Assuming renderer=None means no rendering.** Since neograph-qybn,
  `renderer=None` means BAML default via `describe_value()`. Raw passthrough
  is gone.
- **Testing render_input directly without testing through _dispatch.** The
  dispatch layer adds the inline-vs-template-ref split. Unit tests on
  `render_input` miss this.
- **Stringifying list[BaseModel] instead of using describe_value.** Lists of
  models should produce BAML notation, not Python repr.
- **Accessing flattened fields in inline prompts.** Flattened fields from
  render_for_prompt BaseModel returns are NOT available in inline `${var}`
  prompts -- only in template-ref `{var}` prompts.

## Additional Resources

### Reference Files

- **`references/rendering-flow.md`** - Step-by-step data flow for both prompt types
