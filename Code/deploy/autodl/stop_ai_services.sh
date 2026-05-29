#!/usr/bin/env bash
set -euo pipefail

pkill -f "Code/AIChat/start.py" >/dev/null 2>&1 || true
pkill -f "Code/Yolo_backend/start.py" >/dev/null 2>&1 || true
pkill -f "cloudflared tunnel" >/dev/null 2>&1 || true

echo "AIChat, Yolo_backend and cloudflared tunnels stopped."
echo "Ollama is left running. Stop it manually with: pkill -f 'ollama serve'"
