"""Pagination utilities."""

from rest_framework import pagination


class CustomPageNumberPagination(pagination.PageNumberPagination):

    page_size = 50
    page_size_query_param = "page_size"
