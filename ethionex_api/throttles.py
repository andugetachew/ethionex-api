from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """5 login attempts per minute per user/IP"""

    scope = "login"
    rate = "5/minute"

    def get_cache_key(self, request, view):
        ident = request.data.get("username", request.META.get("REMOTE_ADDR"))
        return self.cache_format % {"scope": self.scope, "ident": str(ident)}


class RegisterRateThrottle(SimpleRateThrottle):
    """3 registration attempts per minute per IP"""

    scope = "register"
    rate = "3/minute"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": request.META.get("REMOTE_ADDR"),
        }


class PasswordResetRateThrottle(SimpleRateThrottle):
    """3 password reset requests per hour per email"""

    scope = "password_reset"
    rate = "3/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": request.data.get("email", request.META.get("REMOTE_ADDR")),
        }


class ProductCreateRateThrottle(SimpleRateThrottle):
    """30 product creations per hour per seller (prevents spam)"""

    scope = "product_create"
    rate = "30/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.user.id}


class ProductUpdateRateThrottle(SimpleRateThrottle):
    """60 product updates per hour per seller"""

    scope = "product_update"
    rate = "60/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.user.id}


class ProductDeleteRateThrottle(SimpleRateThrottle):
    """20 product deletions per hour per seller"""

    scope = "product_delete"
    rate = "20/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.user.id}


class ProductBulkUploadRateThrottle(SimpleRateThrottle):
    """5 bulk uploads per hour per seller"""

    scope = "product_bulk"
    rate = "5/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.user.id}


class CartRateThrottle(SimpleRateThrottle):
    """60 cart operations per minute per user"""

    scope = "cart"
    rate = "60/minute"

    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            return self.cache_format % {
                "scope": self.scope,
                "ident": request.META.get("REMOTE_ADDR"),
            }
        return self.cache_format % {"scope": self.scope, "ident": request.user.id}


class OrderRateThrottle(SimpleRateThrottle):
    """10 orders per minute per user (prevents spam)"""

    scope = "order"
    rate = "10/minute"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.user.id}


class ReviewRateThrottle(SimpleRateThrottle):
    """10 reviews per hour per user"""

    scope = "review"
    rate = "10/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.user.id}


class SearchRateThrottle(SimpleRateThrottle):
    """30 searches per minute (prevents abuse)"""

    scope = "search"
    rate = "30/minute"

    def get_cache_key(self, request, view):
        ident = (
            request.user.id
            if request.user.is_authenticated
            else request.META.get("REMOTE_ADDR")
        )
        return self.cache_format % {"scope": self.scope, "ident": str(ident)}


class SellerDashboardRateThrottle(SimpleRateThrottle):
    """20 dashboard requests per minute"""

    scope = "seller_dashboard"
    rate = "20/minute"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.user.id}


class AdminRateThrottle(SimpleRateThrottle):
    """Admin actions have higher limits but still protected"""

    scope = "admin"
    rate = "200/minute"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.user.id}
