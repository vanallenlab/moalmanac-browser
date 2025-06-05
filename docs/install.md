# Molecular Oncology Almanac - Browser
The Molecular Oncology Almanac browser (herein after referred to as "the service" or "service") is developed with Flask and served with Gunicorn and Nginx on an Ubuntu 18.04 machine hosted on Google Compute Engine. 

## Installation and set up
The Molecular Oncology Almanac browser uses Python 3.6.
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration
### Secret Key
To run the Molecular Oncology Almanac browser, a new file named `secret_key.py` must be added and it must contain:

    GCP_SECRET_KEY='<a secret key>'
    USERNAME='<any username>'
    PASSWORD='<any password>'

You can generate a secret key using:

    $ python
    >>> import os
    >>> os.urandom(50)
    '\xfa\xf0\x02\xaf\xc9\xb5\xc2\xe9\x9a\x1bj\xbaU\xf6\xe5\xe6\xb1\xd1C\xa1\xf9\xfb=u\x883k::-\xe7Q\xca@\x14q\\/\x1db\x7f\xa2)\xa7\xf8\xeb\x8cW\x14\xba'
    # Copy the returned string into secret_key.py.

Do not call `os.urandom` in `secret_key.py`; this will cause the secret key to change every time the Molecular Oncology Almanac browser is restarted, invalidating all current user sessions. You only need to generate the secret key once, at first installation on a system.

`GCP_SECRET_KEY` is used by Flask to cryptographically sign data stored in browser cookies; view [the Flask documentation for more information](http://flask.pocoo.org/docs/1.0/quickstart/#sessions).

`USERNAME` AND `PASSWORD` are specify credentials for logging into the /approve page, to review and approve given submitted entries. 

### config.py
`config.py` contains several configuration variables; for most of them, the provided defaults suffice. The following variables may need to be changed by the user:

|Variable|Description|Example|
|--------|-----------|-------|
|SQLALCHEMY_DATABASE_URI|Contains the path to the SQLite database holding Almanac data. Must begin with the `sqlite://` scheme name followed by a path.|`'sqlite:///db_versions/almanac.0.4.0.sqlite3'`|
|APP_NAME|The full name of the web app; provided to HTML templates.|`The Molecular Oncology Almanac`|
|APP_NAME_SHORT|The short name of the web app; provided to HTML templates.|`Molecular Oncology Almanac`|
|DEBUG|If `True`, enables Flask debugging features; **must be set to `False` in production environments or will create a security risk.**|`False`|
