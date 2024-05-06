docker_image(
    name="mediadata-deps",
    image_tags=["deps"],
    build_platform=["linux/amd64"],
    registries=["mediadata_ai_blocklist"],
    repository="app",
    skip_push=True,
    source="Dockerfile.deps",
)

file(name="app.json", source="app.json")

docker_image(
    name="mediadata-srcs",
    image_tags=["srcs"],
    build_platform=["linux/amd64"],
    registries=["mediadata_ai_blocklist"],
    repository="app",
    skip_push=True,
    source="Dockerfile.srcs",
)

docker_image(
    name="mediadata_ai_blocklist",
    build_platform=["linux/amd64"],
    dependencies=[":mediadata-srcs", ":mediadata-deps", ":app.json"],
    image_tags=[
        "{build_args.VERSION}",
        "latest",
    ],
    source="Dockerfile",
)
