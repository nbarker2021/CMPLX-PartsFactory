# Memory Layer: Docker Compose Synthesis Session
# Session Date: 2026-05-12
# Agent: CMPLX Agent (Primary)

## What Was Done

Synthesized ALL discovered Docker/agent compose templates into a single unified orchestration for CMPLX-PartsFactory. This was not a simple copy — it was a deliberate extraction of patterns from 6+ sources, merged into one coherent system.

## Source Material

1. **opencode-docker-agent** (Downloads zip)
   - Pattern: PUID/PGID user mapping, gosu privilege drop
   - Pattern: Docker socket mount for host Docker control
   - Pattern: HOST_PROJECT_DIR identity mount (same path inside container)
   - Pattern: Entrypoint script handling user/group setup
   - Pattern: docker-compose.dind.yml for sandboxed builds
   - Pattern: docker-compose.web.yml and .server.yml as mode overlays

2. **opencode_agent_ecosystem_mvp** (Downloads zip)
   - Pattern: Root-go + 3 workers + Python controller hub
   - Pattern: Per-agent config/secrets/logs volume mounts
   - Pattern: AGENT_ROLE environment variable
   - Pattern: Auth-based healthchecks (Basic auth + wget)
   - Pattern: CORS configuration for cross-origin worker communication
   - Pattern: Python FastAPI controller on port 8775

3. **CMPLX-Monorepo** (Downloads zip)
   - Pattern: com.cmplx.service and com.cmplx.tier Docker labels
   - Pattern: MCP servers (mcp-postgres, mcp-mmdb, mcp-vector)
   - Pattern: 12 CMPLX family stub services
   - Pattern: Global routing layer (gateway, service-discovery, circuit-breaker, health-aggregator)
   - Pattern: IPAM subnet configuration (172.28.0.0/16)
   - Pattern: Runtime containers for multiple languages

4. **CMPLXUNI** (Downloads zip)
   - Pattern: The Library service
   - Pattern: External network references

5. **Existing workspace compose files**
   - docker-compose.cmplx-unified.yml: CMPLX services (manny-runtime, speedlight, tarpit, snap, mmdb, mdhg)
   - ResearchCraft/docker-compose.yml: Postgres, redis, minio, ollama, observability
   - docker-compose.morphon-graph.yml: Morphon topology with nanoclaw variants
   - MASTER_COMPOSE_WAVES.md: Wave staging, profile map, data-plane binds

## Synthesis Output

### Master Orchestration
- **docker-compose.yml**: 40+ services, 13 profiles, single network (cmplx-backend)
- **docker-compose.web.yml**: Web mode overlay
- **docker-compose.server.yml**: Server mode overlay
- **docker-compose.dind.yml**: Docker-in-Docker overlay

### Container Image
- **Dockerfile.opencode**: node:22-bookworm-slim base
  - Docker CLI + Compose v2 + Buildx
  - GitHub CLI
  - Python 3 + full CMPLX deps
  - OpenCode (npm global)
  - gosu for privilege dropping
  - Entrypoint script for user mapping

### Scripts
- **scripts/bootstrap-env.sh**: Auto-detects WSL, paths, user IDs
- **scripts/opencode-entrypoint.sh**: User/group setup, Docker socket matching
- **scripts/self-compose**: Helper for in-container compose calls

### Profiles
| Profile | Services |
|---------|----------|
| (default) | postgres, redis, rabbitmq, minio, opencode-session, cmplx-unified-api |
| llm | ollama |
| cognitive | manny-runtime, speedlight, snap, mmdb, mdhg |
| bond | tarpit-api |
| field | doc-intel, data-intel, manny-manifold |
| families | 12 family stubs |
| global | gateway, service-discovery, circuit-breaker, health-aggregator |
| mcp | mcp-server, mcp-mmdb, mcp-postgres, mcp-vector |
| controller | workforce-controller (Python hub) |
| discord | discord-bridge |
| observability | prometheus, grafana |
| dind | docker (Docker-in-Docker) |
| full | Everything |

## Three-Space Architecture

The opencode-session container mounts all three doctrinal spaces:
- `/mnt/d/PartsFactory` → `/workspace/PartsFactory` (RW)
- `/mnt/d/Manny Unification 2` → `/workspace/MannyUnification2` (RO)
- `/mnt/d/OC build` → `/workspace/OCbuild` (RO)

Plus Docker socket for host control, and OpenCode state directories for persistence.

## Known Gaps

1. Several referenced services lack actual implementations (they're build contexts in compose):
   - services/workforce-controller/ (needs Python FastAPI controller)
   - services/mcp-*/ (needs MCP server stubs)
   - services/speedlight-api/, tarpit-api/, snap-unified/, mmdb-unified/, mdhg-unified/
   - services/doc-intel/, data-intel/, daemon-unified/

2. 12 family services and 4 global routing services are Flask one-liner stubs

3. No Grafana dashboards created yet

4. Discord token in .env needs rotation (exposed in git history)

## How to Use

```bash
cd /mnt/d/PartsFactory/CMPLX-PartsFactory
./scripts/bootstrap-env.sh          # create .env
docker compose up -d                # core only
docker compose --profile full up -d # everything
```

## Verification

All 4 existing smoke tests pass.
New stub services are not yet tested but have healthcheck endpoints.

## Next Recommended Actions

1. Implement workforce-controller Python FastAPI service
2. Port actual CMPLX service implementations from work/unified/
3. Replace Flask stubs with real family implementations
4. Create Grafana dashboards
5. Rotate Discord bot token
6. Test full stack with `docker compose --profile full up -d`

---

*Memory layer written by CMPLX Agent*
*Reference: docs/SESSION_CHECKIN_2026-05-12.md*
