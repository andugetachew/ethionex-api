from rest_framework.pagination import PageNumberPagination, CursorPagination

from rest_framework.response import Response
from rest_framework.pagination import (
    PageNumberPagination,
    CursorPagination as DRFCursorPagination,
)


class StandardPagination(PageNumberPagination):
    """Standard pagination for most list endpoints (20 per page)"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            {
                "status": "success",
                "data": {
                    "count": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                    "current_page": self.page.number,
                    "page_size": self.page.paginator.per_page,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "results": data,
                },
            }
        )


class LargePagination(PageNumberPagination):
    """Admin endpoints (50 per page)"""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            {
                "status": "success",
                "data": {
                    "count": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                    "current_page": self.page.number,
                    "page_size": self.page.paginator.per_page,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "results": data,
                },
            }
        )


class SmallPagination(PageNumberPagination):
    """Mobile/Reviews (10 per page)"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            {
                "status": "success",
                "data": {
                    "count": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                    "current_page": self.page.number,
                    "page_size": self.page.paginator.per_page,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "results": data,
                },
            }
        )


class CursorPagination(DRFCursorPagination):
    """Cursor pagination for infinite scroll endpoints"""

    page_size = 20
    ordering = "created_at"
