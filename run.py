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
        choices=['http://localhost:8000', 'https://api.moalmanac.org'],
        default=os.environ.get('API_URL', 'http://localhost:8000'),
        help='URL for the MOAlmanac API'
    )
    arg_parser.add_argument(
        '-c', '--config',
        default='config.ini'
    )
    args = arg_parser.parse_args()

    host = os.environ.get('FLASK_HOST', 'localhost')
    port = os.environ.get('FLASK_PORT', 4000)
    debug = True

    app = create_app(config_path=args.config, api=args.api)
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()

api_url = os.environ.get('API_URL', 'https://api.moalmanac.org')
config_path = os.environ.get('APP_CONFIG', 'config.ini')
app = create_app(config_path=config_path, api=api_url)
