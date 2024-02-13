python_sources(
  name="lib",
  dependencies=[
    "3rdparty/py:requirements-all#requests",
    "3rdparty/py:requirements-all#sentry-sdk",
    "3rdparty/py:requirements-all#environs",
  ]
)

pex_binary(
    name="pesacheck-deps",
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
    name="pesacheck-srcs",
    environment=parametrize("__local__", "linux"),
    dependencies=[
        ":lib",
    ],
    entry_point="main.py",
    include_requirements=False,
    include_tools=True,
    layout="packed",
)
