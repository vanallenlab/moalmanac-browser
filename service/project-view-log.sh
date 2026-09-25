#!/bin/bash
# Usage: bash project-view-log.sh [instance]
# Views logs for every browser instance, or only the given one (e.g. ie).

INSTANCE=${1:-*}

sudo journalctl -u "moalmanac-browser@$INSTANCE"
