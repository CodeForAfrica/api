docker_image(
    name="twoopstracker-deps",
    image_tags=["deps"],
    # We just need to hardcode something in the registries so that we can
    # reference it the final image's COPY instructions. Can be anything
    registries=["twoopstracker"],
    repository="app",
    skip_push=True,
    source="Dockerfile.deps",
)

docker_image(
    name="twoopstracker-srcs",
    image_tags=["srcs"],
    registries=["twoopstracker"],
    repository="app",
    skip_push=True,
    source="Dockerfile.srcs",
)

docker_image(
    name="twoopstracker",
    dependencies=[
        ":twoopstracker-deps",
        ":twoopstracker-srcs",
        "twoops_tracker/sh/cmd.sh",
    ],
    image_tags=[
        "{build_args.VERSION}",
        "latest",
    ],
)
