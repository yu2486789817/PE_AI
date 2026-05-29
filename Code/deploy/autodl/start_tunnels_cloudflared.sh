#!/usr/bin/env bash
# ============================================================
# 用 cloudflared 快速隧道把 AutoDL 上的 AI 服务暴露到公网
# 无需公网 VPS、自带 HTTPS，Render 后端可直接调用生成的地址。
# 为 Yolo(8000) 和 AIChat(5000) 各开一个隧道。
#
# 用法：先 bash start_ai_services_cpu.sh 起好服务，再 bash 本脚本
# ============================================================
set -euo pipefail

LOG_DIR="${LOG_DIR:-/root/autodl-tmp/PE_AI/logs}"
YOLO_PORT="${YOLO_PORT:-8000}"
AICHAT_PORT="${AICHAT_PORT:-5000}"

mkdir -p "$LOG_DIR"

# ---------- 安装 cloudflared ----------
if ! command -v cloudflared >/dev/null 2>&1; then
  echo "Installing cloudflared..."
  curl -fsSL -o /usr/local/bin/cloudflared \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x /usr/local/bin/cloudflared
fi

# 清掉旧隧道
pkill -f "cloudflared tunnel" >/dev/null 2>&1 || true
sleep 1

start_tunnel () {
  local name="$1" port="$2" logfile="$3"
  echo "Starting cloudflared tunnel for $name (localhost:$port)..."
  nohup cloudflared tunnel --no-autoupdate --url "http://localhost:$port" \
    > "$logfile" 2>&1 &
}

start_tunnel "Yolo"   "$YOLO_PORT"   "$LOG_DIR/tunnel_yolo.log"
start_tunnel "AIChat" "$AICHAT_PORT" "$LOG_DIR/tunnel_aichat.log"

# ---------- 等待并抓取生成的公网地址 ----------
echo "Waiting for tunnel URLs..."
extract_url () {
  local logfile="$1"
  for _ in $(seq 1 30); do
    local url
    url="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$logfile" 2>/dev/null | head -n1 || true)"
    if [ -n "$url" ]; then
      echo "$url"
      return 0
    fi
    sleep 1
  done
  echo "(未获取到，请查看 $logfile)"
}

YOLO_URL="$(extract_url "$LOG_DIR/tunnel_yolo.log")"
AICHAT_URL="$(extract_url "$LOG_DIR/tunnel_aichat.log")"

echo
echo "============================================================"
echo "公网地址（填到 Render 后端环境变量，保存后 Manual Deploy）："
echo "  YOLO_BASE_URL   = $YOLO_URL"
echo "  AICHAT_BASE_URL = $AICHAT_URL"
echo "============================================================"
echo "隧道日志："
echo "  $LOG_DIR/tunnel_yolo.log"
echo "  $LOG_DIR/tunnel_aichat.log"
echo
echo "注意：trycloudflare 地址在隧道重启后会变化，变了需同步更新 Render 环境变量。"
