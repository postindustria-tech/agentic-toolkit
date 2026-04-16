# Neograph Bug Pattern Catalog

Bugs discovered in production, with root cause and lesson learned. Use this
to recognize recurring patterns.

## Pattern 1: Rendering Asymmetry (neograph-qybn)

**Symptom**: Tool results rendered as BAML, prompt inputs passed as raw Pydantic objects.
**Root cause**: `render_input(model, renderer=None)` returned raw at line 216-217 of renderers.py. `_render_single()` only called when renderer was not None.
**Fix**: BAML default via `describe_value()` when no renderer configured.
**Lesson**: Two code paths that should produce the same format but diverge when a config option is absent. Test both paths on the same instance.

## Pattern 2: Inline Prompt Dotted Access (neograph-x3gz)

**Symptom**: `${claim.text}` in inline prompt resolved to empty string.
**Root cause**: `_render_input` BAML-rendered dict values before `_compile_prompt` ran. `_resolve_var` did `getattr(baml_string, "text")` which returned `""`.
**Fix**: Skip rendering for inline prompts (var substitution needs raw models). BAML-render BaseModel values in `_resolve_var` leaf resolution.
**Lesson**: Rendering order matters. Inline prompts need raw data for dotted access. Template-ref prompts need rendered data for prompt_compiler.

## Pattern 3: Sub-construct Port Remapping (neograph-0h3x)

**Symptom**: Template `{load_uc_composite}` crashed with KeyError inside sub-construct.
**Root cause**: Inside sub-constructs, port params are remapped to `neo_subgraph_input` by `_construct_builder.py:541`. The template referenced the original param name.
**Fix**: lint validates template placeholders against predicted input keys.
**Lesson**: The IR-level key name differs from the @node parameter name inside sub-constructs.

## Pattern 4: Bridge Alias Divergence (neograph-yws3)

**Symptom**: `{research_packet}` passed lint via `--known-vars` but crashed at runtime.
**Root cause**: Consumer bridge aliased `explore_tool_log` to `research_packet`, but inside a sub-construct the actual key was `explore_internal_tool_log`.
**Fix**: lint warns on `known_vars`-only placeholders.
**Lesson**: `--known-vars` gives false confidence. Prefer actual parameter names over bridge aliases.

## Pattern 5: Field-Inside-Model Reference (neograph-vkiw)

**Symptom**: Template `{existing_si}` crashed — it's a field inside UCComposite, not a top-level key.
**Root cause**: After BAML rendering, models arrive as opaque strings keyed by parameter name. Field-level access requires `${param.field}` syntax, not `{field}`.
**Fix**: lint with `template_resolver` reads template text and validates `{placeholder}` names.
**Lesson**: Template-ref prompts are opaque to lint without a resolver. Provide one via `--setup`.

## Pattern 6: Checkpoint Resume (neograph-zs0r)

**Symptom**: Pipeline restarted from scratch instead of resuming from checkpoint.
**Root cause**: `run(graph, input={...})` passed input to `invoke()`, which LangGraph treats as "start new". Resume requires `invoke(None)`.
**Fix**: `_has_existing_checkpoint()` detects saved state and routes to `invoke(None)`.
**Lesson**: LangGraph's `invoke(input)` vs `invoke(None)` distinction is the resume mechanism.

## Pattern 7: Null Coercion (neograph-qqel)

**Symptom**: Pydantic ValidationError — null passed to string field.
**Root cause**: LLM returned `null` for a field with a default value. Pydantic rejects null for non-Optional fields.
**Fix**: `_apply_null_defaults()` recursively replaces null with field defaults before validation.
**Lesson**: LLMs produce null for any field they're uncertain about, regardless of schema.

## Pattern 8: Bare Exception Handlers (neograph-bjin)

**Symptom**: Silent failures — errors swallowed by `except Exception: pass`.
**Root cause**: 13 bare exception handlers across the codebase, added during rapid development.
**Fix**: Replaced all with specific exception types or re-raise. Added structural guard.
**Lesson**: `except Exception: pass` is never acceptable. Structural guard prevents regression.

## Pattern 9: Lint/Runtime Divergence for Inline Flattened Fields (neograph-b3ox)

**Symptom**: Lint passed for `${summary}` in inline prompt, but runtime crashed with unresolvable placeholder.
**Root cause**: `_predict_input_keys` used `include_flattened=True` for both inline and template-ref prompts. Flattened fields from `render_for_prompt()` BaseModel returns are only available in template-ref prompts -- inline prompts skip `_render_with_flattening`.
**Fix**: `_predict_input_keys(node, include_flattened=False)` for inline prompts; `include_flattened=True` (default) for template-ref.
**Lesson**: Lint must mirror the exact key set each prompt type sees at runtime. Different prompt types = different valid keys.

## Pattern 10: Known Extras Not Available in Inline Prompts (neograph-3r4f)

**Symptom**: `${node_id}` in inline prompt resolved to empty string at runtime, but lint didn't warn.
**Root cause**: `_KNOWN_EXTRAS` (node_id, project_root, human_feedback) were included in valid keys for inline prompts. But inline prompts resolve via `_resolve_var()` which only has the raw input dict -- no access to config/state where these live.
**Fix**: Subtract `_KNOWN_EXTRAS` from valid keys for inline prompts: `valid_keys = predicted_keys | (known_vars - _KNOWN_EXTRAS)`.
**Lesson**: Framework-injected keys are only available in the template-ref path where prompt_compiler receives them as kwargs.

## Pattern 11: render_prompt Inspector Divergence (neograph-7io8)

**Symptom**: `render_prompt(node, data)` produced different output than the actual LLM dispatch path.
**Root cause**: `render_prompt` in `_llm.py` built its own `RenderedInput` but didn't use the same `_render_input()` dispatcher logic that the mode dispatch layer uses.
**Fix**: `render_prompt` now calls `build_rendered_input()` from `renderers.py`, same function the dispatch layer uses.
**Lesson**: Inspection tools must use the same code path as execution. Separate re-implementations drift.

## Pattern 12: XmlRenderer No Escaping (neograph-4vtb)

**Symptom**: Input data containing `<` or `&` characters produced malformed XML in prompts.
**Root cause**: `XmlRenderer` concatenated string values directly into XML tags without escaping special characters.
**Fix**: Applied `xml.sax.saxutils.escape()` to string values before tag insertion.
**Lesson**: Any renderer that produces structured text must escape content characters that have special meaning in the format.

## Pattern 13: list[BaseModel] Stringified Instead of BAML (neograph-6w6i)

**Symptom**: A `list[Claim]` in a template-ref prompt rendered as `[Claim(text='...', ...)]` (Python repr) instead of BAML notation.
**Root cause**: `_render_single()` only checked `isinstance(value, BaseModel)`, missing the `list[BaseModel]` case. Lists fell through to `str(value)`.
**Fix**: Added `isinstance(value, list) and value and isinstance(value[0], BaseModel)` check before the primitive fallthrough, routing to `describe_value()`.
**Lesson**: Collection types containing models need explicit rendering dispatch. Don't assume model detection covers collections.

## Pattern 14: Overlapping Flattened Fields Silent Loss (neograph-j3hw)

**Symptom**: Two upstream nodes both had `render_for_prompt()` returning BaseModels with a `summary` field. One silently overwrote the other in `RenderedInput.flattened`.
**Root cause**: `build_rendered_input()` merged flattened fields from all inputs into one dict. Same-named fields from different upstreams collided.
**Fix**: Flattened fields from later inputs overwrite earlier ones (last-write-wins), with a debug log warning when collision occurs.
**Lesson**: Flattened field names share a flat namespace. Field name collisions are possible and should at minimum be logged. Consider namespace-prefixing if this becomes common.

## Pattern 15: render_for_prompt list Return Raw Passthrough (neograph-jmms)

**Symptom**: `render_for_prompt()` returning a `list[BaseModel]` was passed through without any rendering -- downstream got raw Python objects in the template.
**Root cause**: `_render_with_flattening()` only checked `isinstance(result, BaseModel)` for the return value. A `list[BaseModel]` return skipped both the BaseModel branch and the string branch, falling to the catch-all which returned empty flattened dict.
**Fix**: Added explicit `isinstance(result, list) and result and isinstance(result[0], BaseModel)` branch in `_render_with_flattening()` that renders via `describe_value()`.
**Lesson**: `render_for_prompt()` can return str, BaseModel, or list[BaseModel]. Each return type needs its own rendering path.
