"""Pagination utilities."""

from rest_framework import pagination


class CustomPageNumberPagination(pagination.PageNumberPagination):
    page_size_query_param = "page_size"
