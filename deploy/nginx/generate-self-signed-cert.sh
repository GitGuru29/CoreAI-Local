#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="/etc/nginx/certs"
CERT_FILE="${CERT_DIR}/coreai-local.crt"
KEY_FILE="${CERT_DIR}/coreai-local.key"
LAN_IP="${1:-${COREAI_LOCAL_IP:-10.113.228.6}}"
HOSTNAME_ALIAS="${2:-${COREAI_LOCAL_HOSTNAME:-coreai-local.local}}"

mkdir -p "${CERT_DIR}"

openssl req -x509 -nodes -newkey rsa:4096 \
  -keyout "${KEY_FILE}" \
  -out "${CERT_FILE}" \
  -days 825 \
  -subj "/CN=${HOSTNAME_ALIAS}" \
  -addext "subjectAltName=DNS:${HOSTNAME_ALIAS},DNS:localhost,IP:${LAN_IP},IP:127.0.0.1"

chmod 600 "${KEY_FILE}"
chmod 644 "${CERT_FILE}"
