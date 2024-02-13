import os.path

from pants.backend.python.util_rules.package_dists import (
    SetupKwargs,
    SetupKwargsRequest,
)
from pants.engine.fs import DigestContents, GlobMatchErrorBehavior, PathGlobs
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import Target
from pants.engine.unions import UnionRule


class VersionedSetupKwargsRequest(SetupKwargsRequest):
    @classmethod
    def is_applicable(cls, _: Target) -> bool:
        # We always use our custom `setup()` kwargs generator for `python_distribution`
        # targets in this repo.
        return True


@rule
async def setup_kwargs_plugin(request: VersionedSetupKwargsRequest) -> SetupKwargs:
    kwargs = {
        "url": "https://github.com/CodeForAfrica/api",
        "author": "Code for Africa",
        "author_email": "tech@codeforafrica.org",
        "license": "MIT",
        "zip_safe": True,
    }
    kwargs |= request.explicit_kwargs.copy()

    # Add classifiers. We preserve any that were already set.
    standard_classifiers = [
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Topic :: Software Development :: Build Tools",
    ]
    kwargs["classifiers"] = [*standard_classifiers, *kwargs.get("classifiers", [])]
    project_urls = {
        "Source": "https://github.com/CodeForAfrica/api",
        "Tracker": "https://github.com/CodeForAfrica/api/issues",
        "Twitter": "https://twitter.com/Code4Africa",
    }
    kwargs["project_urls"] = {**project_urls, **kwargs.get("project_urls", {})}

    # version can be set to directly or via version_file relative to the BUILD file.
    version = kwargs.get("version", None)
    # version_file is not a standard kwarg, hence we need to pop it from kwargs.
    version_file = kwargs.pop("version_file", None)
    if version and version_file:
        raise ValueError(
            f"The python_distribution target {request.target.address} has supplied both"
            " `version` and `version_file` in its setup_py's kwargs. Only one of these"
            " should be supplied."
        )
    # we default to checking VERSION file if both version and version_file are not set
    if not version:
        version_file = version_file or "VERSION"
        build_file_path = request.target.address.spec_path
        version_path = os.path.join(build_file_path, version_file)
        digest_contents = await Get(
            DigestContents,
            PathGlobs(
                [version_path],
                description_of_origin=(
                    f"the 'version_file' kwarg in {request.target.address}"
                ),
                glob_match_error_behavior=GlobMatchErrorBehavior.error,
            ),
        )
        kwargs["version"] = digest_contents[0].content.decode().strip()

    return SetupKwargs(kwargs, address=request.target.address)


def rules():
    return (
        *collect_rules(),
        UnionRule(SetupKwargsRequest, VersionedSetupKwargsRequest),
    )
