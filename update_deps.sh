#!/bin/sh

pip-compile --output-file=requirements.txt pyproject.toml
pip-compile --extra=mysql --output-file=mysql-requirements.txt pyproject.toml
pip-compile --extra=postgresql --output-file=postgresql-requirements.txt pyproject.toml
pip-compile --extra=ldap --output-file=ldap-requirements.txt pyproject.toml
pip-compile --extra=dev --output-file=dev-requirements.txt pyproject.toml
pip-compile --extra=test --output-file=test-requirements.txt pyproject.toml
