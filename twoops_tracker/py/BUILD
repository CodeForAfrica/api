python_sources(
    name = "lib",
    dependencies = [
        "twoops_tracker/py/twoopstracker",
        # settings.py
        "3rdparty/py:requirements-all#django-cors-headers",
        "3rdparty/py:requirements-all#django-storages",
        "3rdparty/py:requirements-all#djangorestframework-simplejwt",
        "3rdparty/py:requirements-all#google-api-python-client",
        "3rdparty/py:requirements-all#google-auth-httplib2",
        "3rdparty/py:requirements-all#google-auth-oauthlib",
        # others
        "3rdparty/py:requirements-dev#psycopg2-binary",
    ],
)

pex_binary(
    name = "tt",
    dependencies = [
        ":lib",
    ],
    entry_point = "tt.py",
)
