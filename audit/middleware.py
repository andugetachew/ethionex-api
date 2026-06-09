from django.utils.deprecation import MiddlewareMixin
from .services import AuditService


class AuditMiddleware(MiddlewareMixin):
    """Middleware to capture request info for audit logging"""

    def process_request(self, request):
        # Store request info for later use in views
        request.audit_ip = self.get_client_ip(request)
        request.audit_user_agent = request.META.get("HTTP_USER_AGENT", "")

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
