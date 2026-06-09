# tests/unit/test_utils.py
import pytest
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from utils.cache_service import CacheService


class TestCacheService:

    def setup_method(self):
        cache.clear()

    def test_get_or_set_calls_callback_once(self):
        """Callback called only on first miss; second call uses cache."""
        calls = []

        def callback():
            calls.append(1)
            return "result"

        r1 = CacheService.get_or_set("test:once", callback, 60)
        r2 = CacheService.get_or_set("test:once", callback, 60)

        assert r1 == "result"
        assert r2 == "result"
        assert len(calls) == 1

    def test_get_or_set_different_keys_both_stored(self):
        r1 = CacheService.get_or_set("key:a", lambda: "A", 60)
        r2 = CacheService.get_or_set("key:b", lambda: "B", 60)
        assert r1 == "A"
        assert r2 == "B"

    def test_get_product_list_key_contains_prefix(self):
        key = CacheService.get_product_list_key()
        assert "products:list" in key

    def test_get_product_list_key_varies_by_page(self):
        k1 = CacheService.get_product_list_key(page=1)
        k2 = CacheService.get_product_list_key(page=2)
        assert k1 != k2

    def test_get_product_detail_key(self):
        key = CacheService.get_product_detail_key(42)
        assert "42" in key

    def test_invalidate_product_list_clears_keys(self):
        with patch("utils.cache_service.cache") as mock_cache:
            CacheService.invalidate_product_list()
            mock_cache.delete_pattern.assert_called_once()

    def test_invalidate_product_detail(self):
        with patch("utils.cache_service.cache") as mock_cache:
            CacheService.invalidate_product_detail(7)
            mock_cache.delete.assert_called_once()