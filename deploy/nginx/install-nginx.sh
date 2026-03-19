#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LAN_IP="${1:-}"
DEFAULT_IP=""
HOSTNAME_ALIAS="${2:-${COREAI_LOCAL_HOSTNAME:-coreai-local.local}}"

if [[ -z "${LAN_IP}" ]]; then
  DEFAULT_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  LAN_IP="${COREAI_LOCAL_IP:-${DEFAULT_IP}}"
fi
NGINX_CONF="/etc/nginx/nginx.conf"
CONF_DIR="/etc/nginx/conf.d"
TARGET_CONF="${CONF_DIR}/coreai-local.conf"
CONF_TEMPLATE="${SCRIPT_DIR}/coreai-local.conf"

if [[ -z "${LAN_IP}" ]]; then
  echo "Could not detect a LAN IP. Pass it explicitly: sudo bash deploy/nginx/install-nginx.sh <lan-ip>" >&2
  exit 1
fi

if [[ -z "${HOSTNAME_ALIAS}" ]]; then
  echo "Hostname alias is empty. Pass it explicitly: sudo bash deploy/nginx/install-nginx.sh <lan-ip> <hostname>" >&2
  exit 1
fi

if [[ ! -f "${NGINX_CONF}" ]]; then
  echo "nginx config not found at ${NGINX_CONF}. Install nginx first." >&2
  exit 1
fi

install -d "${CONF_DIR}"
install -d /etc/nginx/certs

if ! grep -Fq "include /etc/nginx/conf.d/*.conf;" "${NGINX_CONF}"; then
  cp "${NGINX_CONF}" "${NGINX_CONF}.bak.coreai-local"
  sed -i '/include       mime.types;/a\    include /etc/nginx/conf.d/*.conf;' "${NGINX_CONF}"
fi

sed \
  -e "s/__COREAI_LOCAL_IP__/${LAN_IP}/g" \
  -e "s/__COREAI_LOCAL_HOSTNAME__/${HOSTNAME_ALIAS}/g" \
  "${CONF_TEMPLATE}" > "${TARGET_CONF}"
bash "${SCRIPT_DIR}/generate-self-signed-cert.sh" "${LAN_IP}" "${HOSTNAME_ALIAS}"

nginx -t
systemctl enable --now nginx.service
systemctl reload nginx

echo "nginx is configured for CoreAI-Local on https://${HOSTNAME_ALIAS} and https://${LAN_IP}"
