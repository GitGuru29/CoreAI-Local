#!/usr/bin/env bash
set -euo pipefail

HOSTNAME_ALIAS="${1:-${COREAI_LOCAL_HOSTNAME:-coreai-local.local}}"
POLL_INTERVAL="${COREAI_LOCAL_MDNS_POLL_SECONDS:-5}"
PUBLISHER_PID=""
CURRENT_IP=""

detect_ip() {
  ip -4 -o addr show scope global up | awk '{print $4}' | cut -d/ -f1 | head -n1
}

stop_publisher() {
  if [[ -n "${PUBLISHER_PID}" ]]; then
    kill "${PUBLISHER_PID}" 2>/dev/null || true
    wait "${PUBLISHER_PID}" 2>/dev/null || true
    PUBLISHER_PID=""
  fi
}

start_publisher() {
  local ip="$1"
  /usr/bin/avahi-publish-address -R "${HOSTNAME_ALIAS}" "${ip}" >/dev/null 2>&1 &
  PUBLISHER_PID=$!
}

cleanup() {
  stop_publisher
}

trap cleanup EXIT INT TERM

while true; do
  NEXT_IP="$(detect_ip || true)"

  if [[ "${NEXT_IP}" != "${CURRENT_IP}" ]]; then
    stop_publisher
    CURRENT_IP="${NEXT_IP}"
    if [[ -n "${CURRENT_IP}" ]]; then
      start_publisher "${CURRENT_IP}"
    fi
  elif [[ -n "${PUBLISHER_PID}" ]] && ! kill -0 "${PUBLISHER_PID}" 2>/dev/null; then
    PUBLISHER_PID=""
    if [[ -n "${CURRENT_IP}" ]]; then
      start_publisher "${CURRENT_IP}"
    fi
  fi

  sleep "${POLL_INTERVAL}"
done
