# Global Query API

Generated: 2026-05-14

## Purpose

`/api/global/query` is the first unified API-layer endpoint above the routed
slices. It lets a caller ask once through `repo-kernel` and fan out across the
live read-only global systems.

It currently queries:

- `memory`: live memory search
- `knowledge`: live knowledge/catalog search
- `geometry`: tarpit stats and unique-system summary context
- `operations`: repo-kernel control-plane health context

## API

- `GET /api/global/query?q=<term>`
- `POST /api/global/query`
- MCP tool `repo_kernel_global_query`

GET parameters:

- `q`: required query string
- `systems`: optional repeated filter, for example
  `systems=memory&systems=knowledge`
- `limit`: max normalized results
- `include_context`: include geometry/operations context records
- `dry_run`: return planned fanout calls without executing

POST body:

```json
{
  "q": "receipt",
  "systems": ["memory", "knowledge", "geometry", "operations"],
  "limit": 20,
  "include_context": true,
  "dry_run": false
}
```

## Examples

```powershell
Invoke-RestMethod "http://localhost:8786/api/global/query?q=receipt&limit=10"
Invoke-RestMethod "http://localhost:8786/api/global/query?q=adapter&systems=knowledge&systems=memory"
Invoke-RestMethod "http://localhost:8786/api/global/query?q=receipt&dry_run=true"
```

## Response Shape

The endpoint returns:

- `schema_version`: currently `2`
- `results`: ranked, deduped direct hits from memory, knowledge, and matching
  geometry records
- `context`: optional control/geometry context that helps interpret the query
- `errors`: per-slice failures without failing the whole query
- `api_layer_needs`: next improvements for ranking tuning and snippets
- `policy`: read-only fanout rules

Each result uses the canonical v2 shape:

- `id`: stable short hash for dedupe
- `system`: global system lane
- `source`: routed upstream service
- `kind`: source-specific record kind
- `title`: display title
- `summary`: compact text summary
- `matched_field`: field that matched or provided context
- `confidence`: numeric confidence when available
- `score`: query ranking score
- `local_refs`: repo/report/source references when available
- `raw`: original upstream payload

## Current Needs

The v2 implementation is still conservative. The next API-layer work is:

1. Tune ranking weights with real user queries and add recency/source-quality
   boosts.
2. Add highlighted snippets.
3. Expand research-api beyond health-only reads.
4. Decide whether geometry context should become query-indexed or stay
   diagnostic/contextual.
