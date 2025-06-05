#!/bin/bash

SITE=$1

sudo apt install python3-certbot-nginx
sudo certbot --nginx -d "$SITE" -d www."$SITE"