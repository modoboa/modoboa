import os


def local_scheme(version):
    return ""


def get_version():
    from setuptools_scm import get_version as default_version

    github_version = os.environ.get("GITHUB_REF_NAME", None)
    github_type = os.environ.get("GITHUB_REF_TYPE", None)
    if github_version is not None and github_type == "tag":
        print(f"GITHUB_REF_NAME found, using version: {github_version}")
        return github_version
    return default_version(local_scheme=local_scheme)
