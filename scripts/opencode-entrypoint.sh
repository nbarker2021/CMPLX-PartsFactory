#!/usr/bin/env bash
# CMPLX OpenCode Session Entrypoint
# Handles user mapping, directory setup, and privilege dropping.
set -euo pipefail

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

# Use the existing "node" user if UID matches (it's in the base image)
if id "node" >/dev/null 2>&1 && [ "$(id -u node)" = "$PUID" ]; then
    USER_NAME="node"
    GROUP_NAME="node"
else
    USER_NAME="opencode"
    GROUP_NAME="opencode"
    if ! getent group "${PGID}" >/dev/null 2>&1; then
        groupadd -g "${PGID}" "${GROUP_NAME}" 2>/dev/null || true
    fi
    if ! id "${USER_NAME}" >/dev/null 2>&1; then
        useradd -m -u "${PUID}" -g "${PGID}" -s /bin/bash "${USER_NAME}" 2>/dev/null || true
    fi
fi

# Match the mounted Docker socket group
if [ -S /var/run/docker.sock ]; then
    SOCK_GID="$(stat -c '%g' /var/run/docker.sock)"
    if ! getent group "${SOCK_GID}" >/dev/null 2>&1; then
        groupadd -g "${SOCK_GID}" dockerhost 2>/dev/null || true
    fi
    usermod -aG "${SOCK_GID}" "${USER_NAME}" 2>/dev/null || true
fi

# Ensure directories exist with correct ownership
install -d -o "${USER_NAME}" -g "${PGID}" \
    /workspace \
    /workspace/PartsFactory \
    /workspace/MannyUnification2 \
    /workspace/OCbuild \
    /workspace/logs \
    /home/"${USER_NAME}"/.local/share/opencode \
    /home/"${USER_NAME}"/.local/state/opencode \
    /home/"${USER_NAME}"/.config/opencode \
    /home/"${USER_NAME}"/.docker \
    /tmp/cmplx 2>/dev/null || true

chown -R "${USER_NAME}:${PGID}" \
    /home/"${USER_NAME}"/.local \
    /home/"${USER_NAME}"/.config \
    /home/"${USER_NAME}"/.docker 2>/dev/null || true

export HOME="/home/${USER_NAME}"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

if [ "${RUN_AS_ROOT:-0}" = "1" ]; then
    exec "$@"
fi

exec gosu "${USER_NAME}" "$@"
