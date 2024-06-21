#!/usr/bin/env python

"""
A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
"""

from os import path

from setuptools import find_packages, setup


if __name__ == "__main__":
    HERE = path.abspath(path.dirname(__file__))

    with open(path.join(HERE, "README.rst")) as readme:
        LONG_DESCRIPTION = readme.read()

    def local_scheme(version):
        """Skip the local version (eg. +xyz of 0.6.1.dev4+gdf99fe2)
        to be able to upload to Test PyPI"""
        return ""

    setup(
        long_description=LONG_DESCRIPTION,
        packages=find_packages(
            exclude=["doc", "test_data", "test_project", "frontend"]
        ),
        include_package_data=True,
        zip_safe=False,
        scripts=["bin/modoboa-admin.py"],
        use_scm_version={"local_scheme": local_scheme},
        extras_require={
            "argon2": ["argon2-cffi >= 16.1.0"],
        },
    )
