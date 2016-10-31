#!/bin/bash

LOG_FILE="logs/flask-$(date +"%F_%H-%M-%S").log"

eval `/broad/software/dotkit/init -b`
use Python-2.7

. venv/bin/activate # venv activation limited to script's shell
echo "Logging to $LOG_FILE"
python run.py 2>&1 | tee "$LOG_FILE"
