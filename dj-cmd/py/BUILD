resource(
    name = "README",
    source = "README.md",
)

resource(
    name = "LICENSE",
    source = "LICENSE",
)

resource(
    name = "setup",
    source = "setup.cfg",
)

resource(
    name = "pyproject",
    source = "pyproject.toml",
)

python_distribution(
    name = "dj-cmd",
    dependencies = [
        "dj-cmd/py/dj_cmd:dj_cmd",
        ":pyproject",
        ":setup",
        ":README",
        ":LICENSE",
        # Dependencies on code to be packaged into the distribution.
        # ":lib",
    ],
    # generate_setup = False,
    provides = python_artifact(
        name = "dj-cmd",
        version = "0.0.1",
    ),
    sdist = False,
)
