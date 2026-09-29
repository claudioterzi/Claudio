#!/usr/bin/env bash
# Avvio CLM-v0.1-8B su un pod RunPod (GPU >= 24 GB) — un solo comando.
# Uso dal Web Terminal del pod:
#   curl -sL https://raw.githubusercontent.com/claudioterzi/Claudio/candidate/scacchiera-clm-rank-20260929/scripts/runpod_clm_start.sh | bash
# Espone l'API CLM sulla porta 8700 (da aggiungere alle HTTP ports del pod).
set -euo pipefail

LOG_DIR=/workspace/clm
mkdir -p "$LOG_DIR"

pip install -q contrastive-lm vllm

if [ ! -s "$LOG_DIR/api_key" ]; then
  openssl rand -hex 24 > "$LOG_DIR/api_key"
fi
export CLM_API_KEY="$(cat "$LOG_DIR/api_key")"

nohup vllm serve Qwen/Qwen3-8B --served-model-name qwen3-8b \
  --runner pooling --max-model-len 2048 --port 8090 > "$LOG_DIR/vllm.log" 2>&1 &

echo "Attendo l'encoder (primo avvio: download ~16 GB)..."
until curl -sf http://127.0.0.1:8090/health > /dev/null; do sleep 10; done

nohup clm-serve --no-ui > "$LOG_DIR/clm.log" 2>&1 &
until curl -sf http://127.0.0.1:8700/health > /dev/null; do sleep 3; done

echo
echo "CLM PRONTO."
echo "URL:    https://${RUNPOD_POD_ID:-<id-pod>}-8700.proxy.runpod.net"
echo "Chiave: salvata in $LOG_DIR/api_key (non incollarla in chat)"
