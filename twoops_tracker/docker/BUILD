docker_image(
    name="twoopstracker-deps",
    build_platform=["linux/amd64"],
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
    build_platform=["linux/amd64"],
    image_tags=["srcs"],
    registries=["twoopstracker"],
    repository="app",
    skip_push=True,
    source="Dockerfile.srcs",
)

docker_image(
    name="twoopstracker",
    build_platform=["linux/amd64"],
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
