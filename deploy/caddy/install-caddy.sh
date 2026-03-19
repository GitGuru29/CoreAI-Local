#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 1
fi

HOSTNAME_ALIAS="${1:-${COREAI_LOCAL_HOSTNAME:-coreai-local.local}}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_FILE="${SCRIPT_DIR}/Caddyfile"
TARGET_FILE="/etc/caddy/Caddyfile"
ROOT_CA_SOURCE="/var/lib/caddy/pki/authorities/local/root.crt"
ROOT_CA_EXPORT="/etc/caddy/coreai-local-root.crt"

if ! command -v caddy >/dev/null 2>&1; then
  echo "caddy is not installed. Install it first: sudo pacman -S --needed --noconfirm caddy" >&2
  exit 1
fi

if [[ -z "${HOSTNAME_ALIAS}" ]]; then
  echo "Hostname alias is empty. Pass it explicitly: sudo bash deploy/caddy/install-caddy.sh <hostname>" >&2
  exit 1
fi

install -d /etc/caddy

if [[ -f "${TARGET_FILE}" ]]; then
  cp "${TARGET_FILE}" "${TARGET_FILE}.bak.coreai-local"
fi

sed \
  -e "s/__COREAI_LOCAL_HOSTNAME__/${HOSTNAME_ALIAS}/g" \
  "${SOURCE_FILE}" > "${TARGET_FILE}"

caddy fmt --overwrite "${TARGET_FILE}"

if systemctl is-enabled --quiet nginx.service 2>/dev/null || systemctl is-active --quiet nginx.service 2>/dev/null; then
  systemctl disable --now nginx.service || true
fi

systemctl enable --now caddy.service
systemctl restart caddy.service

# Install the local Caddy root CA into the Linux trust store.
caddy trust --config "${TARGET_FILE}" || true

for _ in $(seq 1 20); do
  if [[ -f "${ROOT_CA_SOURCE}" ]]; then
    install -Dm644 "${ROOT_CA_SOURCE}" "${ROOT_CA_EXPORT}"
    break
  fi
  sleep 1
done

echo "Caddy is serving CoreAI-Local on https://${HOSTNAME_ALIAS}"
echo "Caddy local root CA exported to: ${ROOT_CA_EXPORT}"
