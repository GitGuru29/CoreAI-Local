#!/usr/bin/env bash
set -eu

CERT_DIR="/etc/nginx/certs"
CERT_FILE="${CERT_DIR}/coreai-local.crt"
KEY_FILE="${CERT_DIR}/coreai-local.key"

mkdir -p "${CERT_DIR}"

openssl req -x509 -nodes -newkey rsa:4096 \
  -keyout "${KEY_FILE}" \
  -out "${CERT_FILE}" \
  -days 825 \
  -subj "/CN=10.113.228.6" \
  -addext "subjectAltName=IP:10.113.228.6,IP:127.0.0.1,DNS:localhost"

chmod 600 "${KEY_FILE}"
chmod 644 "${CERT_FILE}"
