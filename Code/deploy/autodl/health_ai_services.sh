#!/usr/bin/env bash
set -euo pipefail

echo "AIChat models:"
curl -sS http://127.0.0.1:5000/api/models
echo
echo
echo "Yolo health:"
curl -sS http://127.0.0.1:8000/health
echo
