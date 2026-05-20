# `cmplx.transform` — Interface

Slot 48 of the attractor frame: **Standalone Geometric Transformer
(Λ⊗E₈ enforced)**. This package supplies the substrate-first
transformer that wires existing CMPLX ports into the familiar
`tokenize → embed → L × block → head → output` shape.

The public surface is small and stable:

```python
from cmplx.transform import GeometricTransformer, TransformerConfig

model = GeometricTransformer(TransformerConfig(num_layers=4))
out = model.forward("any ribbon content")
out.ribbon_out      # canonical output
out.final_morphon   # evolved morphon
out.cache_key       # SpeedLight-style key (stable across forwards)
out.receipts        # full audit trail
out.layer_traces    # per-layer summaries
```

## Components

| Class | Role |
|---|---|
| `MorphonicTokenizer` | DeterministicTokenizer + GeoTokenizer + Morphon forge, NLAECNF canonicalisation, optional ETP program |
| `MorphonicAttention` | MORSR pulse / traverse / scan over the diagnostic port |
| `MorphonicFFN` | TarPit `derive`/`run_program` over the symbolic port, with optional toolkit passes |
| `GeometricTransformerLayer` | One block: attention → NSL gate → FFN → NSL gate → SpeedLight residual |
| `GeometricTransformer` | Full stack: embed → N × layer → eversion head |

## Outputs

`TransformerOutput` carries:

- `ribbon_out` — canonical JSON / ETP / raw projection depending on `output_mode`
- `final_morphon` — the morphon after every layer's evolution
- `cache_key` — deterministic key derived from input ribbon, config digest, and morphon id
- `receipts` — `cmplx.receipt` Receipt instances minted along the way
- `layer_traces` — `LayerTrace` per layer with attention + FFN summaries and ΔΦ
- `speedlight_hit` — True if the full forward was returned from cache

## Settings

The configuration tree is purely data; see `config.py`:

- `TransformerConfig` — top-level (layer count, hidden dim, hooks, output mode)
- `LayerConfig` — per-block (attention, FFN, NSL mode, residual toggle)
- `AttentionConfig` — mirrors `MORSRPolicy` plus `mode: pulse|traverse|scan`
- `FFNConfig` — TarPit dimension, max steps, program length, toolkit passes
- `TokenizerConfig` — DeterministicTokenizer + GeoTokenizer knobs

Changing `attention.max_stages`, `attention.shell_factors`, `attention.gate_mode`,
or `attention.mode` changes the attention trace observably.

## TMN mapping

| TMN | Knob |
|---|---|
| TMN1 | `hook_pre_layer` / `hook_post_layer` |
| TMN2 | `mmdb_path` + SpeedLight residual per layer |
| TMN3 | `num_layers` |
| TMN4 | `HiddenState.brain_observations` |

## Torch wrapper

`cmplx.transform.torch.GeometricTransformerModule` is a thin
`torch.nn.Module` around the numpy core. The substrate stays numpy;
torch buffers expose the last cache key and morphon id only.

## Substrate, multistream, compose (production)

| Surface | Role |
|---------|------|
| `CorpusIngester` / `ingest_multistream` | EN hub + native/math/notation sidecars |
| `translate_hub_from_env` | `CMPLX_TRANSLATE_HUB=noop` (default passthrough) |
| `IndexSupervisor` | SP walk; digits 2–4 run `convolve` / `involute` / `abstract` |
| `compose_pipeline` | Supervisor → `shell.complete` → optional forward |
| `ProductionTransformerConfig()` | N-ladder + shell bind + ports on init |
| `CrystalPackager` | Bundle v2.1.0 (`token_index.sqlite`, links, optional morph sigs) |
| `TokenToolPass` | TarPit `derive`, SNAP labels, `token_geometry` upsert |

### CLI (`python -m cmplx.transform`)

| Command | Purpose |
|---------|---------|
| `ingest` | Single-stream corpus ingest |
| `refine --target-coverage` | Mutation rounds toward slot coverage |
| `template-stats` | Forced-cell / slot coverage report |
| `morph-probe` | Surface morphism verdict |
| `admit` / `complete` | Shell gate |
| `crystallize` / `crystal-info` | Workstate bundle |
| `forward --production [--crystal]` | Production inference profile |

Repo-kernel (read-only): `GET /api/morphonic/status`, `crystal-info`, `template-stats`.

## HF adapter — admit-mask export (platform bridge)

`cmplx.transform.torch.hf_adapter.HuggingFaceAdapterStub` is a boundary stub for
external trainers. Full `PreTrainedModel` integration is out of scope; the contract
is the **admit mask** over indexed concat windows.

| Export | Semantics |
|--------|-----------|
| `export_admit_mask(tokens: list[str]) -> list[bool]` | One bool per token; `True` iff `MorphonShell.admit(concat[:8].ljust(8,"a"))` admits |
| `HFAdapterConfig.admit_mask_export` | When `False`, returns all `True` (mask disabled) |
| `HFAdapterConfig.production` | Builds `ProductionTransformerConfig` for `forward()` demos |

Trainer integration sketch:

1. Load crystal bundle → `CrystalPackager.load` → pass `loaded.shell` into the adapter.
2. Batch candidate tokens from your corpus; call `export_admit_mask` before loss.
3. Filter or weight batches where mask is `True`; rejected tokens stay in the index witness but skip gradient steps.
4. For inference, use `forward --production --crystal <bundle>` or `GeometricTransformer(ProductionTransformerConfig(), shell=...)`.

Env: repo-kernel reads `MORPHONIC_TOKEN_INDEX_DB` and `MORPHONIC_CRYSTAL_BUNDLE` (see production runbook).
