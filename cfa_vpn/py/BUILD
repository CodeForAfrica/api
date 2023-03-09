python_sources(
    name="src",
    dependencies=[
        "cfa_vpn/py/emails",

        "3rdparty/py:requirements-all#outline-vpn-api",
        "3rdparty/py:requirements-all#sendgrid",
        "3rdparty/py:requirements-all#environs",
        "3rdparty/py:requirements-all#python-dotenv",
    ],
)

pex_binary(
    name="outline_manager",
    dependencies = [
        ":src",
    ],
    entry_point="main.py",
)
