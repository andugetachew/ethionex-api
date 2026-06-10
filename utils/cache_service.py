"""
Complete Cache Service for EthioNex API
Handles Redis caching, invalidation, and key generation
"""

from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from functools import wraps
import hashlib
import json
from typing import Any, Callable, Optional


class CacheService:
    """Centralized caching service for EthioNex API"""

    TTL_PRODUCT_LIST = 300  # 5 minutes
    TTL_PRODUCT_DETAIL = 900  # 15 minutes
    TTL_SELLER_DASHBOARD = 600  # 10 minutes
    TTL_CATEGORIES = 3600  # 1 hour
    TTL_CART = 300  # 5 minutes (use cautiously)
    TTL_HOMEPAGE = 600  # 10 minutes

    @staticmethod
    def get_product_list_key(
        page: int = 1, page_size: int = 20, filters: dict = None
    ) -> str:
        """Generate cache key for product list with filters"""
        filters_str = json.dumps(filters or {}, sort_keys=True)
        return f"products:list:p{page}:s{page_size}:{hashlib.md5(filters_str.encode()).hexdigest()}"

    @staticmethod
    def get_product_detail_key(product_id: int) -> str:
        """Generate cache key for product detail"""
        return f"products:detail:{product_id}"

    @staticmethod
    def get_seller_dashboard_key(user_id: int) -> str:
        """Generate cache key for seller dashboard"""
        return f"seller:dashboard:{user_id}"

    @staticmethod
    def get_categories_key() -> str:
        """Generate cache key for categories list"""
        return "categories:list"

    @staticmethod
    def get_cart_key(user_id: int) -> str:
        """Generate cache key for user cart"""
        return f"cart:user:{user_id}"

    @staticmethod
    def get_homepage_key() -> str:
        """Generate cache key for homepage data"""
        return "homepage:data"

    @staticmethod
    def invalidate_product_list() -> None:
        """Invalidate all product list caches"""
        cache.delete_pattern("products:list:*")

    @staticmethod
    def invalidate_product_detail(product_id: int) -> None:
        """Invalidate product detail cache"""
        cache.delete(CacheService.get_product_detail_key(product_id))

    @staticmethod
    def invalidate_product(product_id: int) -> None:
        """Invalidate all caches related to a product"""
        CacheService.invalidate_product_detail(product_id)
        CacheService.invalidate_product_list()

    @staticmethod
    def invalidate_seller_dashboard(user_id: int) -> None:
        """Invalidate seller dashboard cache"""
        cache.delete(CacheService.get_seller_dashboard_key(user_id))

    @staticmethod
    def invalidate_categories() -> None:
        """Invalidate categories cache"""
        cache.delete(CacheService.get_categories_key())

    @staticmethod
    def invalidate_cart(user_id: int) -> None:
        """Invalidate user cart cache"""
        cache.delete(CacheService.get_cart_key(user_id))

    @staticmethod
    def invalidate_homepage() -> None:
        """Invalidate homepage cache"""
        cache.delete(CacheService.get_homepage_key())

    @staticmethod
    def get_or_set(key: str, callback: Callable, ttl: int = TTL_PRODUCT_LIST) -> Any:
        """Get from cache or execute callback and store result"""
        cached_value = cache.get(key)
        if cached_value is not None:
            return cached_value

        value = callback()
        if value is not None:
            cache.set(key, value, ttl)
        return value

    @staticmethod
    def set(key: str, value: Any, ttl: int = TTL_PRODUCT_LIST) -> None:
        """Store value in cache"""
        cache.set(key, value, ttl)

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        return cache.get(key)

    @staticmethod
    def delete(key: str) -> None:
        """Delete value from cache"""
        cache.delete(key)

    @staticmethod
    def delete_pattern(pattern: str) -> None:
        """Delete all keys matching pattern"""
        cache.delete_pattern(pattern)

    @staticmethod
    def clear() -> None:
        """Clear entire cache (use with caution)"""
        cache.clear()


def cache_response(ttl: int = CacheService.TTL_PRODUCT_LIST, key_prefix: str = ""):
    """
    Decorator to cache API responses.
    Usage: @cache_response(ttl=300, key_prefix='products')
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Generate cache key from request
            cache_key = f"{key_prefix}:{request.path}:{request.GET.urlencode()}"
            if key_prefix:
                cache_key = f"{key_prefix}:{request.path}:{request.GET.urlencode()}"

            cached_response = CacheService.get(cache_key)
            if cached_response:
                return cached_response

            response = view_func(self, request, *args, **kwargs)

            if response.status_code == 200:
                CacheService.set(cache_key, response, ttl)

            return response

        return wrapper

    return decorator
