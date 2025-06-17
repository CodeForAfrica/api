python_sources(
    name="lib",
    dependencies=[
        "3rdparty/py:requirements-all#aiohttp",
        "3rdparty/py:requirements-all#backoff",
        "3rdparty/py:requirements-all#pyairtable",
        "3rdparty/py:requirements-all#scrapy",
        "content_access_bot/py/pipeline.py:lib"
    ],
)

pex_binary(
    name="content_access_bot-deps",
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
    name="content_access_bot-srcs",
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
    name="content_access_bot",
    dependencies=[
        ":lib",
    ],
    entry_point="main.py",
)
