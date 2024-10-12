from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    last_page_strings = ("last",)
    page_size_query_param = "page_size"
    max_page_size = 100
