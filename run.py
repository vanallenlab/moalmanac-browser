import argparse
import dotenv
import os

from app import create_app

dotenv.load_dotenv(override=False)

def main():
    """
    Configure and run application when calling run.py directly, for development.
    """
    arg_parser = argparse.ArgumentParser(
        prog='Molecular Oncology Almanac Browser',
        description='Web browser the Molecular Oncology Almanac database'
    )
    arg_parser.add_argument(
        '-a', '--api',
        choices=[
            'http://localhost:8080', 
            'http://127.0.0.1:8000',
            'https://api.moalmanac.org'
        ],
        default=os.environ.get('API_URL', 'http://localhost:8080'),
        help='URL for the MOAlmanac API: http://localhost:8080 (local), http://127.0.0.1:8000 (VM), or https://api.moalmanac.org (live)'
    )
    arg_parser.add_argument(
        '-c', '--config',
        default=os.environ.get('APP_CONFIG', 'deploy/default/config.ini'),
        help='Path to the instance config file, e.g. deploy/ie/config.ini'
    )
    args = arg_parser.parse_args()

    host = os.environ.get('FLASK_HOST', 'localhost')
    port = os.environ.get('FLASK_PORT', 4000)
    debug = True

    app = create_app(config_path=args.config, api=args.api, api_public=os.environ.get('API_PUBLIC_URL'))
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()

# Used by gunicorn in production. API_URL is the local API instance on the same host, while API_PUBLIC_URL is the
# address rendered into pages for users.
api_url = os.environ.get('API_URL', 'http://127.0.0.1:8000')
api_public_url = os.environ.get('API_PUBLIC_URL', 'https://api.moalmanac.org')
config_path = os.environ.get('APP_CONFIG', 'deploy/default/config.ini')
app = create_app(config_path=config_path, api=api_url, api_public=api_public_url)
