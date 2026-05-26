#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/autodl-tmp/PE_AI}"
LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5-pe-sports:q4_k_m}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
YOLO_BASE_URL="${YOLO_BASE_URL:-http://127.0.0.1:8000}"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi

if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "Starting Ollama..."
  nohup env OLLAMA_HOST=127.0.0.1:11434 ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
  sleep 5
fi

if ! ollama list | grep -q "qwen2.5-pe-sports"; then
  echo "Importing Ollama model..."
  (cd Code/AIChat/ollama && ollama create "$OLLAMA_MODEL" -f Modelfile)
fi

python -m venv .venv-ai
source .venv-ai/bin/activate
python -m pip install --upgrade pip
python -m pip install -r Code/AIChat/requirements.txt
python -m pip install -r Code/Yolo_backend/requirements.txt

pkill -f "Code/AIChat/start.py" >/dev/null 2>&1 || true
pkill -f "Code/Yolo_backend/start.py" >/dev/null 2>&1 || true

echo "Starting Yolo_backend on 0.0.0.0:8000..."
nohup env YOLO_HOST=0.0.0.0 YOLO_PORT=8000 \
  python Code/Yolo_backend/start.py > "$LOG_DIR/yolo.log" 2>&1 &

echo "Starting AIChat on 0.0.0.0:5000..."
nohup env AICHAT_HOST=0.0.0.0 AICHAT_PORT=5000 \
  OLLAMA_BASE_URL="$OLLAMA_BASE_URL" \
  OLLAMA_MODEL="$OLLAMA_MODEL" \
  YOLO_BASE_URL="$YOLO_BASE_URL" \
  LOAD_HISTORY_ON_CREATE=background \
  python Code/AIChat/start.py > "$LOG_DIR/aichat.log" 2>&1 &

echo "Started."
echo "Logs:"
echo "  $LOG_DIR/ollama.log"
echo "  $LOG_DIR/aichat.log"
echo "  $LOG_DIR/yolo.log"
echo
echo "Health checks:"
echo "  curl http://127.0.0.1:5000/api/models"
echo "  curl http://127.0.0.1:8000/health"
