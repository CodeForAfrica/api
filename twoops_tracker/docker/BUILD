docker_image(
    name = "twoops-tracker",
    dependencies = [
        "twoops_tracker/py:main",
        "twoops_tracker/sh:sh",
    ],
    image_tags = [
        "{build_args.VERSION}",
        "latest",
    ],
)
