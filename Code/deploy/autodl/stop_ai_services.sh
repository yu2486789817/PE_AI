#!/usr/bin/env bash
set -euo pipefail

pkill -f "Code/AIChat/start.py" >/dev/null 2>&1 || true
pkill -f "Code/Yolo_backend/start.py" >/dev/null 2>&1 || true

echo "AIChat and Yolo_backend stopped."
echo "Ollama is left running. Stop it manually with: pkill -f 'ollama serve'"
