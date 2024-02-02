python_sources(
  name="lib",
  dependencies=[
    "3rdparty/py:requirements-all#requests",
    "3rdparty/py:requirements-all#sentry-sdk",
    "3rdparty/py:requirements-all#environs",
  ]
)

pex_binary(
  name='pesacheck_meedan_bridge',
  entry_point='service.py',
  include_tools=True,
   dependencies=[":lib"],
   layout="packed",
)

