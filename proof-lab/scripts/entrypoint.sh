#!/bin/sh
set -eu

cd "${PROOF_LAB_ROOT:-/workspace/CMPLX-PartsFactory}"

echo "[proof-lab] installing editable packages from mounted clone..."
pip install -q --upgrade pip setuptools wheel
pip install -q -e "./packages/lattice-forge[all]"
pip install -q -e ".[dev]"
pip install -q -e "./packages/lattice-forge-testkit-mcp"

mkdir -p proof-lab/artifacts/meta proof-lab/artifacts/bundles

python proof-lab/scripts/record_clone_meta.py || true

export PYTHONPATH="/workspace/CMPLX-PartsFactory/proof-lab:/workspace/CMPLX-PartsFactory/src:/workspace/CMPLX-PartsFactory/packages/lattice-forge/src:${PYTHONPATH:-}"

case "${PROOF_LAB_MODE:-serve}" in
  serve)
    exec python -m uvicorn proof_lab.server:app --host 0.0.0.0 --port "${PROOF_LAB_PORT:-8871}"
    ;;
  testkit-mcp)
    exec python -m uvicorn lattice_forge_testkit_mcp.server:app --host 0.0.0.0 --port "${TESTKIT_MCP_PORT:-8872}"
    ;;
  verify-once)
    exec make -C proof-lab formal-bundle
    ;;
  backwalk-build)
    pip install -q -e "./packages/lattice-forge[all]"
    if [ "${BACKWALK_PHASE:-pilot}" = "full24" ] && [ -z "${BACKWALK_INVOLUTION_LIMIT:-}" ]; then
      export BACKWALK_INVOLUTION_LIMIT=50
    fi
    export LATTICE_FORGE_WORK_DB=/data/backwalk_work.db
    set -- lattice-forge-backwalk \
      --phase "${BACKWALK_PHASE:-pilot}" \
      --work-db /data/backwalk_work.db \
      --progress-jsonl /data/progress.jsonl \
      --baseline-report /data/baseline_report.json \
      --include-exceptionals "${BACKWALK_EXCEPTIONALS:-g2,f4,e6}"
    if [ -n "${BACKWALK_RESUME:-}" ]; then
      set -- "$@" --resume
    fi
    if [ -n "${BACKWALK_INVOLUTION_LIMIT:-}" ]; then
      set -- "$@" --involution-limit "${BACKWALK_INVOLUTION_LIMIT}"
    fi
    exec "$@"
    ;;
  lattice-space-exhaustion)
    pip install -q -e "./packages/lattice-forge[all]"
    export LATTICE_FORGE_WORK_DB=/data/backwalk_work.db
    set -- lattice-forge-lattice-space --work-db /data/backwalk_work.db
    if [ -n "${BACKWALK_RESUME:-}" ] || [ -n "${LATTICE_SPACE_RESUME:-}" ]; then
      set -- "$@" --resume
    fi
    exec "$@"
    ;;
  backwalk-weyl-orchestrate)
    pip install -q -e "./packages/lattice-forge[all]"
    export LATTICE_FORGE_WORK_DB=/data/backwalk_work.db
    set -- lattice-forge-weyl-bond --work-db /data/backwalk_work.db --resume
    if [ -n "${WEYL_BOND_MAX_ROWS_PER_BATCH:-}" ]; then
      set -- "$@" --max-rows-per-batch "${WEYL_BOND_MAX_ROWS_PER_BATCH}"
    fi
    if [ -n "${WEYL_BOND_BATCH_SLEEP_MS:-}" ]; then
      set -- "$@" --sleep-ms "${WEYL_BOND_BATCH_SLEEP_MS}"
    fi
    exec "$@"
    ;;
  *)
    echo "Unknown PROOF_LAB_MODE=$PROOF_LAB_MODE" >&2
    exit 1
    ;;
esac
