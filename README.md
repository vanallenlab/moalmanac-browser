Web browser for the [Molecular Oncology Almanac](https://moalmanac.org) [database](https://github.com/vanallenlab/moalmanac-db), viewable at: [moalmanac.org](https://moalmanac.org).

## Installation 
### Download

This repository can be downloaded through GitHub by either using the website or terminal. To download on the website, navigate to the top of this page, click the green `Clone or download` button, and select `Download ZIP` to download this repository in a compressed format. To install using GitHub on terminal, type:

```bash
git clone https://github.com/vanallenlab/moalmanac-browser.git
cd moalmanac-browser
```

### Python dependencies
This repository uses Python 3.12. We recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) and running Python with either [Anaconda](https://www.anaconda.com/download/) or [Miniconda](https://conda.io/miniconda.html). 

Run the following from this repository's directory to create a virtual environment and install dependencies with Anaconda or Miniconda:
```bash
conda create -y -n moalmanac-browser python=3.12
conda activate moalmanac-browser
pip install -r requirements.txt
```

Or, if using base Python: 
```bash
virtualenv venv
source activate venv/bin/activate
pip install -r requirements.txt
```

## Usage
The Molecular Oncology Almanac web browser supports multiple configurable instances, each defined by a folder under [deploy/](deploy). Each instance has its own configuration file, https set up, and dedicated SQLite cache. [Our API](https://github.com/vanallenlab/moalmanac-api) provides the data source for the local SQLite3 cache, which is populated according to the settings in the selected config file.

### Updating local caches
To update a local cache, run:

```bash
python -m app.populate_database \
  --api http://127.0.0.1:8000 \
  --config deploy/default/config.ini \
  --drop-tables
```

To update multiple local caches, append `--config` multiple times. For example:

```bash
python -m app.populate_database \
  --api http://127.0.0.1:8000 \
  --config deploy/default/config.ini \
  --config deploy/ie/config.ini \
  --config deploy/ca/config.ini \
  --drop-tables
```

### Instances

Each instance is defined by a folder under the [`deploy/`](deploy) directory, containing a `config.ini` and an `nginx.conf`. The instance is selected with the `APP_CONFIG` environment variable, or `--config` when running [run.py](run.py). For example, to launch the Ireland instance for development:

```bash
python run.py --config deploy/ie/config.ini
```

Each instance reads its own local SQLite cache from `data/`, named by `[app] cache` in its config, so multiple instances can run from the same checkout.

### Environment configuration

Flask configuration variables are managed using environment files:

- [.env](.env) - used for local development
- [.env.production](.env.production) - used for production, loaded with systemd 

| Variable | Description |
|---|---|
| `API_URL` | API used by the server to request data. In production, this is the API instance running on the same VM, `http://127.0.0.1:8000`. |
| `API_PUBLIC_URL` | API address shown to users in links, such as `https://api.moalmanac.org`. Defaults to `API_URL`. |
| `APP_CONFIG` | Instance config file, such as `deploy/default/config.ini`. In production, this is set per instance by systemd. |
| `GUNICORN_WORKERS`, `GUNICORN_THREADS` | Gunicorn workers and threads per instance, used in production. |

To launch the application for development, using variables from [.env](.env):
```bash
python run.py
```

### Production deployment

All browser instances and [our API](https://github.com/vanallenlab/moalmanac-api) are hosted on the same VM behind one nginx, and browser instances request data from the local API rather than over the internet. See [service/README.md](service/README.md) for set up.

This repository uses [Gunicorn](https://gunicorn.org) to serve the Flask application for production. Each instance runs from the [systemd template unit, service/moalmanac-browser@.service](service/moalmanac-browser@.service), where the instance name (e.g. `moalmanac-browser@ie`) selects `deploy/<instance>/config.ini`. Environment variables are set from [.env.production](.env.production) via the `EnvironmentFile` variable:

```ini
EnvironmentFile=/home/breardon/moalmanac-browser/.env.production
Environment="APP_CONFIG=/home/breardon/moalmanac-browser/deploy/%i/config.ini"
```

Gunicorn is launched using the provided `ExecStart` command:

```ini
/home/breardon/mambaforge-pypy3/envs/moalmanac-browser/bin/gunicorn --worker-class gthread --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --bind unix:moalmanac-browser-%i.sock -m 007 run:app
```

Systemd and Gunicorn manage launching the application for production, so there is no need to run `python run.py` for production use.

## Citation

If you find this tool or any code herein useful, please cite:  
> [Reardon, B., Moore, N.D., Moore, N.S., *et al*. Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology. *Nat Cancer* (2021). https://doi.org/10.1038/s43018-021-00243-3](https://www.nature.com/articles/s43018-021-00243-3)

## Disclaimer - For research use only
DIAGNOSTIC AND CLINICAL USE PROHIBITED. DANA-FARBER CANCER INSTITUTE (DFCI) and THE BROAD INSTITUTE (Broad) MAKE NO REPRESENTATIONS OR WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING, WITHOUT LIMITATION, WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NONINFRINGEMENT OR VALIDITY OF ANY INTELLECTUAL PROPERTY RIGHTS OR CLAIMS, WHETHER ISSUED OR PENDING, AND THE ABSENCE OF LATENT OR OTHER DEFECTS, WHETHER OR NOT DISCOVERABLE.

In no event shall DFCI or Broad or their Trustees, Directors, Officers, Employees, Students, Affiliates, Core Faculty, Associate Faculty and Contractors, be liable for incidental, punitive, consequential or special damages, including economic damages or injury to persons or property or lost profits, regardless of whether the party was advised, had other reason to know or in fact knew of the possibility of the foregoing, regardless of fault, and regardless of legal theory or basis. You may not download or use any portion of this program for any non-research use not expressly authorized by DFCI or Broad. You further agree that the program shall not be used as the basis of a commercial product and that the program shall not be rewritten or otherwise adapted to circumvent the need for obtaining permission for use of the program other than as specified herein.
