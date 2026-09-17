#!/usr/bin/env bash
# Uso: ./fastapi.sh <workers>   -> reinicia a FastAPI no host com N workers
set -euo pipefail
W="${1:-1}"
[ -f resultados/uvicorn.pid ] && kill "$(cat resultados/uvicorn.pid)" 2>/dev/null && sleep 2 || true
mkdir -p resultados
nohup .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers "$W" > "resultados/uvicorn_${W}w.log" 2>&1 &
echo $! > resultados/uvicorn.pid
sleep 4
echo "uvicorn com $(grep -c 'Started server process' resultados/uvicorn_${W}w.log) worker(s), pid $(cat resultados/uvicorn.pid)"
