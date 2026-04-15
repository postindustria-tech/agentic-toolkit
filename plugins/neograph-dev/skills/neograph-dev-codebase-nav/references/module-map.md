# Module Ownership Map

Complete listing of `src/neograph/` modules with responsibilities and import rules.

## DX Layer (user-facing API surfaces)

| Module | Lines | Owns | Imports from |
|--------|-------|------|-------------|
| `decorators.py` | ~722 | `@node`, `@merge_fn`, `construct_from_functions`, `construct_from_module`, mode inference, DI classification | `_construct_builder`, `_sidecar`, `_di_classify`, `modifiers` |
| `forward.py` | ~885 | `ForwardConstruct`, tracer, symbolic proxies, `_BranchNode` | `construct`, `compiler`, `node` |

## IR Layer (internal representation)

| Module | Lines | Owns | Imports from |
|--------|-------|------|-------------|
| `node.py` | ~271 | `Node` model, `Tool`, mode enum, `Node.scripted()` | `modifiers` |
| `construct.py` | ~150 | `Construct` model, assembly-time validation trigger | `_construct_validation`, `node` |
| `modifiers.py` | ~605 | `Each`, `Oracle`, `Operator`, `Loop`, `Modifiable`, `ModifierSet` | `node` (for type checking) |
| `_construct_validation.py` | ~761 | Validator walker, `effective_producer_type`, fan-in checks, loop validation | `node`, `construct` (via TYPE_CHECKING) |

## Compiler Layer

| Module | Lines | Owns | Imports from |
|--------|-------|------|-------------|
| `compiler.py` | ~450 | `compile()`, `describe_graph()`, subgraph wiring, Operator edges | `state`, `factory`, `_construct_validation` |
| `state.py` | ~372 | `compile_state_model()`, state field generation, reducers | `node`, `modifiers` |

## Runtime Dispatch Layer

| Module | Lines | Owns | Imports from |
|--------|-------|------|-------------|
| `factory.py` | ~626 | `_extract_input`, `make_subgraph_fn`, `register_scripted`, `register_tool_factory`, `register_condition` | `_dispatch`, `_oracle`, `_registry`, `node` |
| `_dispatch.py` | ~290 | `ModeDispatch` protocol, `ThinkDispatch`, `ToolDispatch`, `ScriptedDispatch`, `_render_input` | `_llm`, `renderers`, `node` |
| `_llm.py` | ~966 | LLM invocation, `invoke_structured`, `invoke_with_tools`, `_compile_prompt`, `_resolve_var`, `_render_tool_result_for_llm`, `configure_llm` | `describe_type`, `renderers`, `tool` |

## Support Modules

| Module | Lines | Owns |
|--------|-------|------|
| `_sidecar.py` | ~120 | PrivateAttr accessors (`_get_sidecar`, `_get_param_res`), merge_fn registry, `infer_oracle_gen_type` |
| `_construct_builder.py` | ~696 | @node assembly: adjacency building, port param detection, scripted shim registration |
| `_di_classify.py` | ~251 | DI binding classification (`_classify_di_params`) |
| `_oracle.py` | ~250 | Oracle/Each runtime wiring helpers |
| `_registry.py` | ~80 | Singleton registry (scripted fns, tool factories, conditions) |
| `renderers.py` | ~258 | `render_input()`, `XmlRenderer`, `DelimitedRenderer`, `JsonRenderer` |
| `describe_type.py` | ~462 | `describe_type()`, `describe_value()`, `ExcludeFromOutput`, BAML notation |
| `lint.py` | ~285 | `lint()`, DI binding checks, template placeholder validation |
| `runner.py` | ~180 | `run()`, checkpoint resume, DI injection |
| `testing.py` | ~638 | `scaffold_tests()`, multi-file test scaffold generator |
| `loader.py` | ~266 | YAML spec loader, type resolution |
| `naming.py` | ~30 | `field_name_for()` — node name to state field name |

## Import Cycle Boundaries

These module pairs CANNOT import each other at top level:

- `decorators.py` <-> `_construct_builder.py` (builder imports sidecar, not decorators)
- `factory.py` <-> `compiler.py` (compiler imports factory, factory does not import compiler)
- `renderers.py` -> `describe_type.py` (one-way, describe_type does not import renderers)
- `_dispatch.py` -> `_llm.py` (one-way, _llm does not import _dispatch)
