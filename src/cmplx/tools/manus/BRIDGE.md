# Manus toolkit bridge

## Provenance

Integrated from `Manus dev and review` (Manny datasets). Original: 30-domain
CMPLX novel tools + `CMPLXToolRegistry` rail adapters for Enhanced Manifold v3.

## Ports consumed

- `geometry` — E8/Leech witnesses and instrument encodings
- `conservation` / `constraints` — manifold admission (via enhanced_v3)
- `receipt` — composite tool receipts (`cmplx.tools.composite`)

## Ports provided

- `CMPLXToolRegistry.adapt(domain, raw_dict) → {alpha, beta, gamma}` 8D rails
- Instrument modules under `instruments/` callable as domain morphons

## Manifest

`manifest_v3.json` — 30 tools, axis requirements, Wolfram class, lane weights.
