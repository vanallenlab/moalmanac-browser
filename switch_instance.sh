#!/bin/bash
# Usage: ./switch-instance.sh default

INSTANCE=$1
DEPLOY_DIR="deploy"

VALID_INSTANCES=($(find "$DEPLOY_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;))

if [ -z "$INSTANCE" ]; then
  echo "Usage: $0 [instance-name]"
  echo "Valid instances: ${VALID_INSTANCES[*]}"
  exit 1
fi

if [[ ! " ${VALID_INSTANCES[*]} " =~ " ${INSTANCE} " ]]; then
  echo "Error: '$INSTANCE' is not a valid instance."
  echo "Valid instances: ${VALID_INSTANCES[*]}"
  exit 1
fi

ln -sf "data/cache-$INSTANCE.sqlite3" data/cache.sqlite3
ln -sf "deploy/$INSTANCE/config.ini" config.ini
ln -sf "deploy/$INSTANCE/nginx.conf" service/moalmanac-browser
ln -sf "deploy/$INSTANCE/secure-application.sh" service/secure-application.sh

echo "Switched to instance: $INSTANCE"