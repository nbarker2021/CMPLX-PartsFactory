# CMPLX-PartsFactory — top-level make targets (delegates proof formal work to proof-lab/)
.PHONY: help proof-lab-install proof-lab-up proof-lab-down proof-lab-verify proof-lab-health proof-lab-export lattice-forge-verify ring1-ring2-quick ring2-quick ring2-verify

help:
	@echo "proof-lab-up       docker compose proof-lab + testkit MCP"
	@echo "proof-lab-verify   POST formal run inside container"
	@echo "proof-lab-health   curl :8871 and :8872 health"
	@echo "lattice-forge-verify  host PowerShell verify script"
	@echo "proof-lab-export   zip latest presentation bundle"
	@echo "empirical-quick    per-claim empirical matrix (quick depths)"
	@echo "ring1-ring2-quick  Ring 1 proofs + audit + Ring 2 (--quick)"
	@echo "ring2-quick        Ring 2 bundle only (--quick)"
	@echo "ring2-verify       Ring 2 bundle + transport regression"

proof-lab-install:
	$(MAKE) -C proof-lab install

proof-lab-up:
	docker compose -f docker-compose.proof-lab.yml up -d --build

proof-lab-down:
	docker compose -f docker-compose.proof-lab.yml down

proof-lab-verify:
	curl -sf http://localhost:8871/health
	curl -sf -X POST http://localhost:8871/api/formal/run

proof-lab-health:
	$(MAKE) -C proof-lab health

proof-lab-export:
	$(MAKE) -C proof-lab export-latest

lattice-forge-verify:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_lattice_forge_family.ps1

ring1-ring2-quick:
	cd packages/lattice-forge && python scripts/run_ring1_ring2_pipeline.py --quick

ring2-quick:
	cd packages/lattice-forge && python scripts/run_ring2_bundle.py --quick

ring2-verify:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_lattice_forge_family.ps1 -Regimes -Ring2
