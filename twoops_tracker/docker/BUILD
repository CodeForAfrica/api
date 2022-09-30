docker_image(
    name = "twoopstracker",
    dependencies = [
        "twoops_tracker/py:main",
        "twoops_tracker/sh:sh",
    ],
    image_tags = [
        "{build_args.VERSION}",
        "latest",
    ],
)
