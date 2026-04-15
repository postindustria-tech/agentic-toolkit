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
