Scripts in this directory are used to serve the application on a Google Compute Engine VM. The VM is shared with [moalmanac-api](https://github.com/vanallenlab/moalmanac-api): a single nginx serves the API and every browser instance, and each browser instance requests data from the API running on the same host (`http://127.0.0.1:8000`) rather than over the internet.

| Service | Domain | systemd unit | Upstream |
|---|---|---|---|
| moalmanac-api | api.moalmanac.org | `moalmanac-api` | `127.0.0.1:8000` |
| moalmanac-browser, default | moalmanac.org (dev.moalmanac.org redirects here) | `moalmanac-browser@default` | `moalmanac-browser-default.sock` |
| moalmanac-browser, ie | ie.moalmanac.org | `moalmanac-browser@ie` | `moalmanac-browser-ie.sock` |
| moalmanac-browser, ca | ca.moalmanac.org | `moalmanac-browser@ca` | `moalmanac-browser-ca.sock` |

Each instance is a folder under [deploy/](../deploy) with a `config.ini` and `nginx.conf`. All instances share one checkout and one Python environment, and run through the systemd template unit [moalmanac-browser@.service](moalmanac-browser@.service), which sets `APP_CONFIG=deploy/<instance>/config.ini`. Each instance reads its own sqlite cache, named by `[app] cache` in its config.

## Installation

1. Create VM. We recommend e2-standard-4 (4 vCPU, 16 GB) with ubuntu-22.04 LTS, as it hosts all four services.
2. Create a static ip address to associate with the VM
3. Add A and CNAME records for every domain above to the zone under network services > cloud dns > and your zone, all pointing to the VM's static ip.
4. Set up moalmanac-api first, following its [service/README.md](https://github.com/vanallenlab/moalmanac-api/blob/main/service/README.md), and confirm it responds with `curl http://127.0.0.1:8000/`.
5. Pull this repo to `/home/breardon/moalmanac-browser` with GitHub and git token, and install requirements into the `moalmanac-browser` environment.
6. Populate each instance's cache from the local API:

   ```bash
   python -m app.populate_database \
     --api http://127.0.0.1:8000 \
     --config deploy/default/config.ini \
     --config deploy/ie/config.ini \
     --config deploy/ca/config.ini \
     --drop-tables
   ```

7. Run `copy_serving_files_and_start_service.sh` to configure gunicorn and nginx for every instance under `deploy/`.
8. Check [this guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04) for additional steps, such as creating a https certificate. This is done through certbot.
9. Run `secure-application.sh` to install https certifications for every instance.

Gunicorn worker and thread counts are set by `GUNICORN_WORKERS` and `GUNICORN_THREADS` in [.env.production](../.env.production), and apply to each instance.

## Adding an instanc

1. Create `deploy/<instance>/` with a `config.ini` (with a unique `[app] cache`) and an `nginx.conf` that proxies to `moalmanac-browser-<instance>.sock`.
2. Populate its cache with `python -m app.populate_database --api http://127.0.0.1:8000 --config deploy/<instance>/config.ini --drop-tables`.
3. Rerun `copy_serving_files_and_start_service.sh`, add the domain to `secure-application.sh`, and rerun it.

## Restart

- `restart-service.sh` to restart nginx and every instance, or `restart-service.sh ie` to restart one instance.

## View logs

- `project-view-log.sh` to view the system log for every instance, or `project-view-log.sh ie` for one instance
- `nginx-view.sh` to view nginx process logs
- `nginx-view-access-log.sh` to view nginx access logs
- `nginx-view-error-log.sh` to view nginx error logs
