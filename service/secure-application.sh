#!/bin/bash
# Usage: bash secure-application.sh
# Requests https certificates for every browser instance. Add a site here when adding an instance under deploy/.

SITES=(moalmanac.org dev.moalmanac.org ie.moalmanac.org ca.moalmanac.org)

DOMAINS=()
for SITE in "${SITES[@]}"; do
  DOMAINS+=(-d "$SITE" -d "www.$SITE")
done

sudo apt install -y python3-certbot-nginx
sudo certbot --nginx "${DOMAINS[@]}"
