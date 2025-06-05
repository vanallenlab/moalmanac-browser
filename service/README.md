# Useful scripts for the web host

Scripts in this directory are used to serve the application on a Google Compute Engine VM.

## Installation
1. Create VM. Used e2-small with ubuntu-22.04 LTS
2. Create a static ip address to associate with the VM
3. Add A and CNAME to zone under network services > cloud dns > and your zone, if you haven't already created one
4. Launch VM, pull repo with GitHub and git token
5. Run `copy_serving_files_and_start_service.sh moalmanac-browser-default` to configure gunicorn and nginx.^1
6. Check [this guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04) for additional steps, such as creating a https certificate. This is done through certbot.
7. Run `secure-application.sh` to install https certifications^2

Note 1: If deploying another instance of this web browser, provide the appropriate file when running `copy_serving_files_and_start_service.sh`; e.g., `copy_serving_files_and_start_service.sh moalmanac-browser-ie`. 

Note 2: The url specified in serving file must also be provided to secure-application.sh. For example, `secure-application.sh dev.moalmanac.org`.

## View logs
- `project-view-log.sh` to view the system log for project
- `nginx-view.sh` to view nginx process logs
- `nginx-view-access.sh` to view nginx access logs
- `nginx-view-error.sh` to view nginx error logs

Add A and CNAME to zone under network services

