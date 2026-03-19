#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
UNIT_SOURCE="${REPO_ROOT}/deploy/systemd/coreai-local-mdns.service"
UNIT_TARGET="/etc/systemd/system/coreai-local-mdns.service"

if [[ ! -x "${SCRIPT_DIR}/publish-mdns-host.sh" ]]; then
  chmod +x "${SCRIPT_DIR}/publish-mdns-host.sh"
fi

if [[ ! -f "${UNIT_SOURCE}" ]]; then
  echo "mDNS unit file not found at ${UNIT_SOURCE}" >&2
  exit 1
fi

install -Dm644 "${UNIT_SOURCE}" "${UNIT_TARGET}"
systemctl daemon-reload
systemctl enable --now avahi-daemon.service
systemctl enable --now coreai-local-mdns.service
systemctl restart coreai-local-mdns.service

echo "mDNS publishing enabled for coreai-local.local"
