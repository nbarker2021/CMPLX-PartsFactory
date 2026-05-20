#!/usr/bin/env bash
# CMPLX Environment Bootstrap
# ============================
# Run this once to set up .env from the template.
# Usage: ./scripts/bootstrap-env.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
ENV_FILE="${PROJECT_DIR}/.env"
TEMPLATE="${PROJECT_DIR}/.env.template"

echo "=== CMPLX-PartsFactory Environment Bootstrap ==="

if [ -f "${ENV_FILE}" ]; then
  echo ".env already exists at ${ENV_FILE}"
  read -p "Overwrite? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Bootstrap cancelled."
    exit 0
  fi
fi

# Detect host paths
if grep -qi microsoft /proc/version 2>/dev/null || [ -n "${WSL_DISTRO_NAME:-}" ]; then
  echo "WSL detected."
  HOST_PF="/mnt/d/PartsFactory"
  HOST_MANNY="/mnt/d/Manny Unification 2"
  HOST_OC="/mnt/d/OC build"
else
  HOST_PF="${HOME}/PartsFactory"
  HOST_MANNY="${HOME}/Manny Unification 2"
  HOST_OC="${HOME}/OC build"
fi

# Detect user/group IDs
PUID="$(id -u)"
PGID="$(id -g)"
DOCKER_GID="$(getent group docker | cut -d: -f3 || echo 998)"

# Create .env from template
cp "${TEMPLATE}" "${ENV_FILE}"

# Replace placeholders
sed -i "s|HOST_PROJECT_DIR=.*|HOST_PROJECT_DIR=${PROJECT_DIR}|" "${ENV_FILE}"
sed -i "s|HOST_PARTS_FACTORY=.*|HOST_PARTS_FACTORY=${HOST_PF}|" "${ENV_FILE}"
sed -i "s|HOST_MANNY_UNIFICATION=.*|HOST_MANNY_UNIFICATION=${HOST_MANNY}|" "${ENV_FILE}"
sed -i "s|HOST_OC_BUILD=.*|HOST_OC_BUILD=${HOST_OC}|" "${ENV_FILE}"
sed -i "s|PUID=.*|PUID=${PUID}|" "${ENV_FILE}"
sed -i "s|PGID=.*|PGID=${PGID}|" "${ENV_FILE}"
sed -i "s|DOCKER_GID=.*|DOCKER_GID=${DOCKER_GID}|" "${ENV_FILE}"

echo ".env created at ${ENV_FILE}"
echo "Please review and edit the file before starting services."
echo ""
echo "Quick start:"
echo "  docker compose up -d"
echo "  docker compose --profile full up -d"
