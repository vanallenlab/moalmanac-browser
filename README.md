# TARGET DB
TARGET DB captures the current body of knowledge on how genetic alterations affect clinical actionability. As the field of precision medicine grows, the quantity of research on how specific alterations affect therapeutic response and patient prognosis expands at an increasing rate. TARGET DB seeks to curate this information from the literature, increasing the abilities of clinicians and researchers alike to rapidly assess the importance of an alteration.

## Configuration
To run the TARGET web portal, a new file named `secret_key.py` must be added and it must contain:

    GCP_SECRET_KEY='<a secret key>'

You can generate a secret key using:

    $ python
    >>> import os
    >>> os.urandom(50)
    '\xfa\xf0\x02\xaf\xc9\xb5\xc2\xe9\x9a\x1bj\xbaU\xf6\xe5\xe6\xb1\xd1C\xa1\xf9\xfb=u\x883k::-\xe7Q\xca@\x14q\\/\x1db\x7f\xa2)\xa7\xf8\xeb\x8cW\x14\xba'
    # Copy the returned string into secret_key.py.

Do not call `os.urandom` in `secret_key.py`; this will cause the secret key to change every time the TARGET portal is restarted, invalidating all current user sessions. You only need to generate the secret key once, at first installation on a system.
