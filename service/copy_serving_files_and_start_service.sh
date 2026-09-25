#!/bin/bash
# Usage: bash copy_serving_files_and_start_service.sh
# Run from the service/ folder, after moalmanac-api has been set up on this VM and the caches have been populated.

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

sudo apt update -y
sudo apt install -y build-essential libssl-dev libffi-dev nginx python3-certbot-nginx
sudo ufw disable

# Before running this script, the moalmanac account must own a conda install at /srv/moalmanac/miniforge3 with this
# repository's environment built in it. See service/README.md.

sudo cp "$REPO_DIR/service/moalmanac-browser@.service" /etc/systemd/system/moalmanac-browser@.service
sudo systemctl daemon-reload

# One systemd service and one nginx site per instance folder under deploy/
for INSTANCE_DIR in "$REPO_DIR"/deploy/*/; do
  INSTANCE=$(basename "$INSTANCE_DIR")
  echo "Configuring instance: $INSTANCE"

  sudo systemctl enable --now "moalmanac-browser@$INSTANCE"

  sudo cp "$INSTANCE_DIR/nginx.conf" "/etc/nginx/sites-available/moalmanac-browser-$INSTANCE"
  sudo ln -sf "/etc/nginx/sites-available/moalmanac-browser-$INSTANCE" /etc/nginx/sites-enabled/
done

sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

sudo chmod 755 /srv/moalmanac
