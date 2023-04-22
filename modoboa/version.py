import os


def local_scheme(version):
    return ""


def get_version():
    from setuptools_scm import get_version as default_version
    github_version = os.environ.get('GITHUB_REF_NAME', None)
    is_release = os.environ.get('IS_RELEASE', None)
    if is_release is not None and github_version is not None:
        print(f"GITHUB_REF_NAME found, using version: {github_version}")
        return github_version
    return default_version(local_scheme=local_scheme)

