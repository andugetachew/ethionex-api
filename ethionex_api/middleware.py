# # ethionex_api/middleware.py
# from django.utils.deprecation import MiddlewareMixin
# import logging
# import time
# import uuid

# logger = logging.getLogger("ethionex")


# class RequestLoggingMiddleware(MiddlewareMixin):
#     """Log all requests and responses"""

#     def process_request(self, request):
#         request.start_time = time.time()
#         request.request_id = str(uuid.uuid4())

#         logger.info(
#             f"Request: {request.method} {request.path}",
#             extra={
#                 "request_id": request.request_id,
#                 "ip": request.META.get("REMOTE_ADDR"),
#                 "user": request.user.id if request.user.is_authenticated else None,
#             },
#         )

#     def process_response(self, request, response):
#         duration = time.time() - request.start_time
#         logger.info(
#             f"Response: {response.status_code} - {duration:.2f}s",
#             extra={
#                 "request_id": getattr(request, "request_id", None),
#                 "duration": duration,
#             },
#         )
#         return response


from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Log the request method and path
        logger.info(f"{request.method} {request.path}")
        return None

    def process_response(self, request, response):
        # Log the response status
        logger.info(f"Response status: {response.status_code}")
        return response
