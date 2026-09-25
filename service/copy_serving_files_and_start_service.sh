#!/bin/bash
# Usage: bash copy_serving_files_and_start_service.sh
# Run from the service/ folder, after moalmanac-api has been set up on this VM and the caches have been populated.

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

sudo apt update -y
sudo apt install -y build-essential libssl-dev libffi-dev nginx python3-certbot-nginx
sudo ufw disable

#sudo wget https://github.com/conda-forge/miniforge/releases/download/24.7.1-0/Mambaforge-pypy3-24.7.1-0-Linux-x86_64.sh
#bash Mambaforge-pypy3-24.7.1-0-Linux-x86_64.sh
# restart shell (close out of VM and open a new one)
# conda create virtual env, make sure that conda is installed correctly
# activate venv and install requirements into it

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

sudo chmod 755 /home/breardon
