resources(
    name="resources",
    sources=[
        "pyproject.toml",
        "setup.cfg",
        "README.md",
        "VERSION",
    ],
)

python_distribution(
    name="dj-cmd",
    dependencies=[
        "dj-cmd/py/dj_cmd:dj_cmd",
        ":resources",
    ],
    provides=setup_py(
        name="dj-cmd",
    ),
    sdist=False,
)
