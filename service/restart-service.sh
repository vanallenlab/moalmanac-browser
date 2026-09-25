#!/bin/bash
# Usage: bash restart-service.sh [instance]
# Restarts every browser instance, or only the given one (e.g. ie).

INSTANCE=${1:-*}

sudo systemctl daemon-reload
sudo systemctl restart nginx
sudo systemctl restart "moalmanac-browser@$INSTANCE"
