from django import http


def test_view(request):
    return http.HttpResponse()
