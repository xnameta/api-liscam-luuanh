#!/bin/bash

set -e

APP_DIR="/root/api-liscam-luuanh"
LOG_FILE="/var/log/liscam-update.log"

cd "$APP_DIR"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') =====" >> "$LOG_FILE"

git fetch origin main >> "$LOG_FILE" 2>&1

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "Khong co code moi." >> "$LOG_FILE"
    exit 0
fi

echo "Phat hien code moi: $LOCAL -> $REMOTE" >> "$LOG_FILE"

git pull --ff-only origin main >> "$LOG_FILE" 2>&1

if [ -f requirements.txt ]; then
    /root/api-liscam-luuanh/venv/bin/pip install -r requirements.txt >> "$LOG_FILE" 2>&1
fi

systemctl restart liscam-api

echo "Cap nhat thanh cong." >> "$LOG_FILE"