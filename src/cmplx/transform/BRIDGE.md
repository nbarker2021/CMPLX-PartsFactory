# `cmplx.transform` — Bridge

The transformer is an **orchestrator**. It does not implement geometry,
symbolic execution, or caching itself; it reads from the
`MorphonController` registry and composes whatever providers are
registered there. All wiring goes through `bridge.py`.

## Ports consumed

| Port | Used by | Purpose |
|---|---|---|
| `diagnostic` | `MorphonicAttention` | MORSR pulse / traverse / scan (sparse geometric probing) |
| `symbolic` | `MorphonicFFN` | TarPit `derive` and `run_program` (ETP execution) |
| `conservation` | `GeometricTransformerLayer` | NSL gate decisions before / after each block |
| `cache` | `GeometricTransformerLayer`, `GeometricTransformer` | SpeedLight residual + whole-forward idempotency |
| `receipt` | `GeometricTransformer` | Mint MINT / GATE / PROCESS receipts on layer boundaries |
| `atlas` | `MorphonicTokenizer` | Optional canonical c-value admission (when registered) |
| `constraints` | `MorphonicTokenizer` | Optional Aletheia admission gate |
| `engine` | (reserved) | Available for `full_manifold_pipeline=True` phase-2 delegation |
| `geometry` | `MorphonicTokenizer` | Optional E8 / Leech coefficient population |

The package does **not** provide a port; the slot it occupies in the
attractor frame is an application-level composition, not a port
contract.

## Static imports

The few hard imports kept inside the package:

- `cmplx.morphon.Morphon, MorphonController, Receipt`
- `cmplx.morsr.{Overlay, MORSRPolicy, ShellMode, StopMetric, TraversalStrategy}` — value types used to translate `AttentionConfig` into MORSR's policy types
- `cmplx.nsl.GateMode` — value type for layer NSL settings
- `cmplx.engine.eversion.network.DeterministicTokenizer, MorphonicEversionNetwork` — eversion tokenizer + head-only delegation
- `cmplx.primitives.core.NLAECNFChain` — canonical key computation
- `runtime.cmplx_bootstrap.register_all` — bootstrapping (lazy)
- `cmplx.services.speedlight_engine_service.GeoTokenizer` — optional, behind a try/except so the substrate import does not pull the services tree on every call

## Bootstrapping

`TransformerConfig(register_ports_on_init=True)` (the default) triggers
`bridge.ensure_bootstrapped(mmdb_path=config.mmdb_path)` from
`GeometricTransformer.__init__`. The bootstrap is module-cached, so
multiple transformers share one registration cycle. Tests that need a
fresh controller can call `bridge.reset_bootstrap_state()` and
`MorphonController.reset_for_tests()` in tandem.

## Morphonic substrate tables (same SQLite)

| Table | Writer |
|-------|--------|
| `token_bonds` | ingest, `TokenIndexBuilder`, `involute` |
| `address_meaning` | ingest, SNAP, `abstract` |
| `translation_links` | multistream ingest |
| `token_geometry` | ingest, `TokenToolPass` |
| `morph_signatures` | tool pass, `morph-probe` |

Warm-start keys (`token_index::neighbor::dr*::*`) are published by `convolve` and the builder via the `cache` port.

## What the transformer does **not** consume

The MVP does not require:

- `embed` — the morphon's 4-Embed view is not used by the layer loop
- `transport` — outputs are returned in-process, no carrier encoding
- `snap` / `crystal` / `routing` — only consulted when the FFN's
  `toolkit_passes` list names them and the corresponding port is
  registered

These remain available for layered configuration but are not on the
default execution path.
