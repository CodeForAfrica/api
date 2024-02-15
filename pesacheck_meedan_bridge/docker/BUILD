docker_image(
    name="pesacheck-deps",
    image_tags=["deps"],
    build_platform=["linux/amd64"],
    registries=["pesacheck_meedan_bridge"],
    repository="app",
    skip_push=True,
    source="Dockerfile.deps",
)

file(name="app.json", source="app.json")

docker_image(
    name="pesacheck-srcs",
    image_tags=["srcs"],
    build_platform=["linux/amd64"],
    registries=["pesacheck_meedan_bridge"],
    repository="app",
    skip_push=True,
    source="Dockerfile.srcs",
)

docker_image(
    name="pesacheck_meedan_bridge",
    build_platform=["linux/amd64"],
    dependencies=[":pesacheck-srcs", ":pesacheck-deps", ":app.json"],
    image_tags=[
        "{build_args.VERSION}",
        "latest",
    ],
    source="Dockerfile",
)
