docker_image(
    name="content_access_bot-deps",
    image_tags=["deps"],
    build_platform=["linux/amd64", "linux/arm64"],
    registries=["content_access_bot"],
    repository="app",
    skip_push=True,
    source="Dockerfile.deps",
)

file(name="app.json", source="app.json")

docker_image(
    name="content_access_bot-srcs",
    image_tags=["srcs"],
    build_platform=["linux/amd64", "linux/arm64"],
    registries=["content_access_bot"],
    repository="app",
    skip_push=True,
    source="Dockerfile.srcs",
)

docker_image(
    name="content_access_bot",
    build_platform=["linux/amd64", "linux/arm64"],
    dependencies=[":content_access_bot-srcs", ":content_access_bot-deps", ":app.json"],
    image_tags=[
        "{build_args.VERSION}",
        "latest",
    ],
    source="Dockerfile",
)
