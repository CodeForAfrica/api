python_sources(
    name="lib",
    dependencies=[
        "3rdparty/py:requirements-all#aiohttp",
        "3rdparty/py:requirements-all#backoff",
        "3rdparty/py:requirements-all#pyairtable",
        "3rdparty/py:requirements-all#python-dotenv",
    ],
)

pex_binary(
    name="mediadata-deps",
    environment=parametrize("__local__", "linux"),
    dependencies=[
        ":lib",
    ],
    entry_point="main.py",
    include_sources=False,
    include_tools=True,
    layout="packed",
)

pex_binary(
    name="mediadata-srcs",
    environment=parametrize("__local__", "linux"),
    dependencies=[
        ":lib",
    ],
    entry_point="main.py",
    include_requirements=False,
    include_tools=True,
    layout="packed",
)


pex_binary(
    name="mediadata",
    dependencies=[
        ":lib",
    ],
    entry_point="main.py",
)
