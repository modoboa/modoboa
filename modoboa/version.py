import os

def get_version():
    from setuptools_scm import get_version as default_version
    github_version = os.environ.get('GITHUB_REF_NAME', None)
    if github_version is not None:
        return github_version

    return default_version(local_scheme="")

