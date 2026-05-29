#!/usr/bin/env bash
# ============================================================
# AutoDL 纯 CPU 实例启动脚本（无 GPU）
# 与 start_ai_services.sh 的区别：
#   - 安装 CPU 版 PyTorch（避免拉 CUDA 大包、避免无 GPU 报错）
#   - 放开线程数，让 32 核 CPU 充分利用（默认按核数自适应）
#   - 传入 YOLO 推理性能参数（跳帧 + 降分辨率）
#   - Ollama 在无 GPU 时自动回退 CPU，无需额外配置
# ============================================================
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/autodl-tmp/PE_AI}"
LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
OLLAMA_MODEL="${OLLAMA_MODEL:-peai}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
YOLO_BASE_URL="${YOLO_BASE_URL:-http://127.0.0.1:8000}"

# CPU 推理调优（可按机器核数 / 视频情况覆盖）
CPU_THREADS="${CPU_THREADS:-$(nproc)}"
PROCESS_SKIP_FACTOR="${PROCESS_SKIP_FACTOR:-3}"
INFER_IMGSZ="${INFER_IMGSZ:-320}"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

# ---------- Ollama（CPU 自动回退）----------
if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi

if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "Starting Ollama (CPU)..."
  nohup env OLLAMA_HOST=127.0.0.1:11434 ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
  sleep 5
fi

if ! ollama list | awk '{print $1}' | grep -qx "$OLLAMA_MODEL"; then
  echo "Importing Ollama model..."
  # 使用与 gguf 同目录、路径正确的 Modelfile（FROM ./xxx.gguf）
  # 需提前把 Code/AIChat/models/qwen2.5-pe-sports.q4_k_m/ 整个目录上传到此处
  (cd Code/AIChat/models/qwen2.5-pe-sports.q4_k_m && ollama create "$OLLAMA_MODEL" -f Modelfile)
fi

# ---------- Python 依赖（CPU 版 PyTorch）----------
python -m venv .venv-ai
source .venv-ai/bin/activate
python -m pip install --upgrade pip
# 先装 CPU 版 torch/torchvision，避免后续 ultralytics 拉到 CUDA 版
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r Code/AIChat/requirements.txt
python -m pip install -r Code/Yolo_backend/requirements.txt

pkill -f "Code/AIChat/start.py" >/dev/null 2>&1 || true
pkill -f "Code/Yolo_backend/start.py" >/dev/null 2>&1 || true

# ---------- Yolo_backend（CPU + 性能调优）----------
echo "Starting Yolo_backend on 0.0.0.0:8000 (CPU, threads=$CPU_THREADS, imgsz=$INFER_IMGSZ, skip=$PROCESS_SKIP_FACTOR)..."
nohup env YOLO_HOST=0.0.0.0 YOLO_PORT=8000 \
  OMP_NUM_THREADS="$CPU_THREADS" \
  MKL_NUM_THREADS="$CPU_THREADS" \
  PROCESS_SKIP_FACTOR="$PROCESS_SKIP_FACTOR" \
  INFER_IMGSZ="$INFER_IMGSZ" \
  python Code/Yolo_backend/start.py > "$LOG_DIR/yolo.log" 2>&1 &

# ---------- AIChat ----------
echo "Starting AIChat on 0.0.0.0:5000..."
nohup env AICHAT_HOST=0.0.0.0 AICHAT_PORT=5000 \
  OLLAMA_BASE_URL="$OLLAMA_BASE_URL" \
  OLLAMA_MODEL="$OLLAMA_MODEL" \
  YOLO_BASE_URL="$YOLO_BASE_URL" \
  LOAD_HISTORY_ON_CREATE=background \
  python Code/AIChat/start.py > "$LOG_DIR/aichat.log" 2>&1 &

echo "Started (CPU mode)."
echo "Logs:"
echo "  $LOG_DIR/ollama.log"
echo "  $LOG_DIR/aichat.log"
echo "  $LOG_DIR/yolo.log"
echo
echo "Health checks:"
echo "  curl http://127.0.0.1:5000/api/models"
echo "  curl http://127.0.0.1:8000/health"
echo
echo "确认线程已放开（应接近 $CPU_THREADS 而非 2）:"
echo "  python -c \"import torch; print(torch.get_num_threads())\""
