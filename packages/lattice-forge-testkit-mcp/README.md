# lattice-forge-testkit-mcp

MCP (SSE) server for **non-proven** lattice-forge work: CONJ claims, Tier B falsify, and selective pytest. The proven formal surface remains the installable `lattice-forge` library and Proof Lab HTTP runner.

## Run (stdio-free SSE)

```bash
pip install -e packages/lattice-forge[all]
pip install -e packages/lattice-forge-testkit-mcp
lf-testkit-mcp
# curl http://localhost:8872/health
# MCP SSE: http://localhost:8872/mcp/sse
```

## Docker

See repo-root `docker-compose.proof-lab.yml` service `lf-testkit-mcp`.

## Cursor MCP config snippet

```json
{
  "mcpServers": {
    "lf-testkit": {
      "url": "http://localhost:8872/mcp/sse"
    }
  }
}
```
