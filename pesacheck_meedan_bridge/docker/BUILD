docker_image(
    name="pesacheck-deps",
    image_tags=["deps"],
    registries=["pesacheck_meedan_bridge"],
    repository="app",
    skip_push=True,
    source="Dockerfile.deps",
)

docker_image(
    name="pesacheck-srcs",
    image_tags=["srcs"],
    registries=["pesacheck_meedan_bridge"],
    repository="app",
    skip_push=True,
    source="Dockerfile.srcs",
)

docker_image(
    name="pesacheck_meedan_bridge",
    dependencies=[':pesacheck-srcs', ':pesacheck-deps'],
    image_tags=[
        "{build_args.VERSION}",
        "latest",
    ],
    source="Dockerfile"
)
