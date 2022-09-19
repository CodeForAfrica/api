python_sources(
    name = "lib",
    dependencies = [
        "twoops_tracker/py/twoopstracker",
        "3rdparty/py:requirements-all#django-cors-headers",
        "3rdparty/py:requirements-all#django-storages",
        "3rdparty/py:requirements-all#djangorestframework-simplejwt",
        "3rdparty/py:requirements-all#google-api-python-client",
        "3rdparty/py:requirements-all#google-auth-httplib2",
        "3rdparty/py:requirements-all#google-auth-oauthlib",
        "3rdparty/py:requirements-all#gunicorn",
        "3rdparty/py:requirements-all#redis",
        # others
        "3rdparty/py:requirements-dev#psycopg2-binary",
    ],
)

pex_binary(
    name = "main",
    dependencies = [
        ":lib",
    ],
    entry_point = "main.py",
)
