# utils/middleware.py
import time
import logging
import uuid

logger = logging.getLogger("ethionex")


class RequestLoggingMiddleware:
    """Middleware to log all requests and responses"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = str(uuid.uuid4())
        request.start_time = time.time()

        logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                "request_id": request.request_id,
                "ip_address": request.META.get("REMOTE_ADDR"),
            },
        )

        response = self.get_response(request)

        duration = time.time() - request.start_time
        logger.info(
            f"Request completed: {request.method} {request.path} - {response.status_code} ({duration:.2f}s)",
            extra={
                "request_id": getattr(request, "request_id", None),
                "status_code": response.status_code,
                "duration": duration,
            },
        )

        return response
