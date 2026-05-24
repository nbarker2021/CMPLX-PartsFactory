# Proof Lab — formal validation (host or inside container)
REPO_ROOT := $(abspath ..)
PKG := $(REPO_ROOT)/packages/lattice-forge
export PROOF_LAB_ROOT := $(REPO_ROOT)
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1
export PYTHONPATH := $(REPO_ROOT)/src:$(PKG)/src

.PHONY: help install verify formal-bundle empirical-quick empirical-materialize docker-up docker-down docker-verify export-latest health

help:
	@echo "Targets: install verify formal-bundle docker-up docker-down docker-verify export-latest health"

install:
	pip install -q --upgrade pip setuptools wheel
	pip install -q -r requirements.txt
	pip install -q -e "$(PKG)[all]"
	pip install -q -e "$(REPO_ROOT)[dev]"
	pip install -q -e "$(REPO_ROOT)/packages/lattice-forge-testkit-mcp"

verify:
	powershell -NoProfile -ExecutionPolicy Bypass -File "$(REPO_ROOT)/scripts/verify_lattice_forge_family.ps1"

formal-bundle:
	python scripts/record_clone_meta.py
	python -c "from proof_lab.runner import run_formal_bundle; import json,sys; r=run_formal_bundle(); print(json.dumps(r,indent=2)); sys.exit(0 if r['ok'] else 1)"

empirical-materialize:
	python packages/lattice-forge/scripts/materialize_empirical_platforms.py

empirical-quick:
	python packages/lattice-forge/scripts/run_empirical_matrix.py --quick

docker-up:
	docker compose -f "$(REPO_ROOT)/docker-compose.proof-lab.yml" up -d --build

docker-down:
	docker compose -f "$(REPO_ROOT)/docker-compose.proof-lab.yml" down

docker-verify:
	curl -sf http://localhost:8871/health
	curl -sf -X POST http://localhost:8871/api/formal/run

export-latest:
	python scripts/export_presentation_bundle.py

health:
	curl -sf http://localhost:8871/health && curl -sf http://localhost:8872/health
