#!/usr/bin/env python

"""
A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
"""

from os import path

try:
    from pip.req import parse_requirements
except ImportError:
    # pip >= 10
    from pip._internal.req import parse_requirements

from setuptools import find_packages, setup


def get_requirements(requirements_file):
    """Use pip to parse requirements file."""
    requirements = []
    if path.isfile(requirements_file):
        for req in parse_requirements(requirements_file, session="hack"):
            try:
                if req.markers:
                    requirements.append("%s;%s" % (req.req, req.markers))
                else:
                    requirements.append("%s" % req.req)
            except AttributeError:
                # pip >= 20.0.2
                requirements.append(req.requirement)
    return requirements


if __name__ == "__main__":
    HERE = path.abspath(path.dirname(__file__))
    INSTALL_REQUIRES = get_requirements(path.join(HERE, "requirements.txt"))
    MYSQL_REQUIRES = get_requirements(path.join(HERE, "mysql-requirements.txt"))
    POSTGRESQL_REQUIRES = get_requirements(
        path.join(HERE, "postgresql-requirements.txt"))
    LDAP_REQUIRES = get_requirements(path.join(HERE, "ldap-requirements.txt"))

    with open(path.join(HERE, "README.rst")) as readme:
        LONG_DESCRIPTION = readme.read()

    def local_scheme(version):
        """Skip the local version (eg. +xyz of 0.6.1.dev4+gdf99fe2)
            to be able to upload to Test PyPI"""
        return ""

    setup(
        name="modoboa",
        description="Mail hosting made simple",
        long_description=LONG_DESCRIPTION,
        license="ISC",
        url="http://modoboa.org/",
        author="Antoine Nguyen",
        author_email="tonio@ngyn.org",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Environment :: Web Environment",
            "Framework :: Django :: 2.2",
            "Intended Audience :: System Administrators",
            "License :: OSI Approved :: ISC License (ISCL)",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Topic :: Communications :: Email",
            "Topic :: Internet :: WWW/HTTP",
        ],
        keywords="email",
        packages=find_packages(exclude=["doc", "test_data", "test_project"]),
        include_package_data=True,
        zip_safe=False,
        scripts=["bin/modoboa-admin.py"],
        install_requires=INSTALL_REQUIRES,
        use_scm_version={"local_scheme": local_scheme},
        python_requires=">=3.4",
        setup_requires=["setuptools_scm"],
        extras_require={
            "ldap": LDAP_REQUIRES,
            "mysql": MYSQL_REQUIRES,
            "postgresql": POSTGRESQL_REQUIRES,
            "argon2": ["argon2-cffi >= 16.1.0"],
        },
    )
