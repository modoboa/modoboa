"""Mocks used for testing."""

import httmock


# Modoboa API mocks

@httmock.urlmatch(
    netloc=r"api\.modoboa\.org$", path=r"^/1/instances/search/", method="post")
def modo_api_instance_search(url, request):
    """Return empty response."""
    return {"status_code": 404}


@httmock.urlmatch(
    netloc=r"api\.modoboa\.org$", path=r"^/1/instances/", method="post")
def modo_api_instance_create(url, request):
    """Simulate successful creation."""
    return {
        "status_code": 201,
        "content": {"pk": 100}
    }


@httmock.urlmatch(
    netloc=r"api\.modoboa\.org$", path=r"^/1/instances/.+/", method="put")
def modo_api_instance_update(url, request):
    """Simulate successful update."""
    return {"status_code": 200}


@httmock.urlmatch(
    netloc=r"api\.modoboa\.org$", path=r"^/1/versions/", method="get")
def modo_api_versions(url, request):
    """Simulate versions check."""
    return {
        "status_code": 200,
        "content": [
            {"name": "modoboa", "version": "9.0.0", "url": ""},
        ]
    }
