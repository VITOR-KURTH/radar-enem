#!/usr/bin/env bash
# Uso: ./rodar_teste.sh <nome> [usuarios] [spawn_rate] [duracao]
# Roda o Locust headless dentro da rede do compose contra o Flask (web_app:5000)
# e salva os CSVs em resultados/<nome>_*.csv
set -euo pipefail
NOME="${1:?nome do teste}"
USERS="${2:-10000}"
RATE="${3:-500}"
TEMPO="${4:-2m}"
mkdir -p resultados
docker run --rm \
  --network radar-enem_radar_network \
  --ulimit nofile=65536:65536 \
  --sysctl net.ipv4.ip_local_port_range="1024 65535" \
  --sysctl net.ipv4.tcp_tw_reuse=1 \
  -v "$PWD/locustfile.py:/mnt/locust/locustfile.py:ro" \
  -v "$PWD/resultados:/mnt/locust/resultados" \
  locustio/locust \
  -f /mnt/locust/locustfile.py \
  --host http://web_app:5000 \
  --headless -u "$USERS" -r "$RATE" -t "$TEMPO" \
  --processes 8 \
  --csv "/mnt/locust/resultados/$NOME" \
  --only-summary
