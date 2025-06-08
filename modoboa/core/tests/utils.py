import os

import requests


try:
    requests.get("https://modoboa.org/")
except requests.ConnectionError:
    HAVE_NETWORK = False
else:
    HAVE_NETWORK = True


def get_doveadm_test_path():
    return f"{os.path.dirname(__file__)}/doveadm"
