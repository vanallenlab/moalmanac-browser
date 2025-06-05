#!/bin/bash
# Usage: ./secure-application.sh

SITE=ie.moalmanac.org

sudo apt install python3-certbot-nginx
sudo certbot --nginx -d "$SITE" -d www."$SITE"