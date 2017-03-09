#!/bin/bash

LOG_FILE="logs/flask-$(date +"%F").log"

. venv/bin/activate # venv activation limited to script's shell
echo "Logging to $LOG_FILE"
echo "["$(basename "$0")"] New session starting $(date +"%F %H:%M:%S")." >> "$LOG_FILE"
python run.py 2>&1 | tee -a "$LOG_FILE"
