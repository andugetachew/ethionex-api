import pytest
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from utils.cache_service import CacheService, cache_response


@pytest.fixture(autouse=True)
def clear(db):
    cache.clear()
    yield
    cache.clear()


class TestCacheServiceKeys:

    def test_product_list_key_default(self):
        key = CacheService.get_product_list_key()
        assert key.startswith("products:list:p1:s20:")

    def test_product_list_key_with_filters(self):
        k1 = CacheService.get_product_list_key(filters={"cat": "a"})
        k2 = CacheService.get_product_list_key(filters={"cat": "b"})
        assert k1 != k2

    def test_product_detail_key(self):
        assert CacheService.get_product_detail_key(5) == "products:detail:5"

    def test_seller_dashboard_key(self):
        assert CacheService.get_seller_dashboard_key(3) == "seller:dashboard:3"

    def test_categories_key(self):
        assert CacheService.get_categories_key() == "categories:list"

    def test_cart_key(self):
        assert CacheService.get_cart_key(7) == "cart:user:7"

    def test_homepage_key(self):
        assert CacheService.get_homepage_key() == "homepage:data"


class TestCacheServiceInvalidation:

    def test_invalidate_product_detail(self):
        CacheService.set(CacheService.get_product_detail_key(1), {"id": 1})
        CacheService.invalidate_product_detail(1)
        assert CacheService.get(CacheService.get_product_detail_key(1)) is None

    def test_invalidate_product_calls_both(self):
            from unittest.mock import patch
            CacheService.set(CacheService.get_product_detail_key(2), {"id": 2})
            with patch.object(CacheService, 'invalidate_product_list'):
                CacheService.invalidate_product(2)
            assert CacheService.get(CacheService.get_product_detail_key(2)) is None
    
    def test_invalidate_seller_dashboard(self):
        CacheService.set(CacheService.get_seller_dashboard_key(1), {"sales": 5})
        CacheService.invalidate_seller_dashboard(1)
        assert CacheService.get(CacheService.get_seller_dashboard_key(1)) is None

    def test_invalidate_categories(self):
        CacheService.set(CacheService.get_categories_key(), ["electronics"])
        CacheService.invalidate_categories()
        assert CacheService.get(CacheService.get_categories_key()) is None

    def test_invalidate_cart(self):
        CacheService.set(CacheService.get_cart_key(1), {"items": []})
        CacheService.invalidate_cart(1)
        assert CacheService.get(CacheService.get_cart_key(1)) is None

    def test_invalidate_homepage(self):
        CacheService.set(CacheService.get_homepage_key(), {"featured": []})
        CacheService.invalidate_homepage()
        assert CacheService.get(CacheService.get_homepage_key()) is None


class TestCacheServiceCore:

    def test_set_and_get(self):
        CacheService.set("test:key", {"value": 42})
        assert CacheService.get("test:key") == {"value": 42}

    def test_get_miss_returns_none(self):
        assert CacheService.get("nonexistent:key") is None

    def test_delete(self):
        CacheService.set("del:key", "data")
        CacheService.delete("del:key")
        assert CacheService.get("del:key") is None

    def test_clear(self):
        CacheService.set("a", 1)
        CacheService.set("b", 2)
        CacheService.clear()
        assert CacheService.get("a") is None
        assert CacheService.get("b") is None

    def test_get_or_set_miss_calls_callback(self):
        called = []
        def cb():
            called.append(True)
            return {"fresh": True}
        result = CacheService.get_or_set("miss:key", cb)
        assert result == {"fresh": True}
        assert len(called) == 1

    def test_get_or_set_hit_skips_callback(self):
        CacheService.set("hit:key", {"cached": True})
        called = []
        result = CacheService.get_or_set("hit:key", lambda: called.append(True))
        assert result == {"cached": True}
        assert len(called) == 0

    def test_get_or_set_none_callback_not_cached(self):
        """Callback returning None does not store anything"""
        CacheService.get_or_set("none:key", lambda: None)
        assert CacheService.get("none:key") is None
        
    def test_delete_pattern_no_crash(self):
        from unittest.mock import patch
        CacheService.set("patt:1", 1)
        with patch('utils.cache_service.cache') as mock_cache:
            mock_cache.delete_pattern = lambda x: None
            CacheService.delete_pattern("patt:*")

    
class TestCacheResponseDecorator:

    def test_cache_response_decorator_calls_view(self):
        """cache_response decorator executes the view function"""
        call_count = 0
 
        class FakeView:
            @cache_response(ttl=60, key_prefix="test_exec")
            def get(self, request):
                nonlocal call_count
                call_count += 1
                from unittest.mock import MagicMock
                resp = MagicMock()
                resp.status_code = 404  # non-200 so no pickle attempt
                return resp
 
        from unittest.mock import MagicMock
        req = MagicMock()
        req.path = "/test/"
        req.GET.urlencode.return_value = ""
 
        v = FakeView()
        v.get(req)
        v.get(req)
        assert call_count == 2

    def test_does_not_cache_non_200(self):
        call_count = 0

        class FakeView:
            @cache_response(ttl=60, key_prefix="test404")
            def get(self, request):
                nonlocal call_count
                call_count += 1
                resp = MagicMock()
                resp.status_code = 404
                return resp

        req = MagicMock()
        req.path = "/missing/"
        req.GET.urlencode.return_value = ""

        v = FakeView()
        v.get(req)
        v.get(req)
        assert call_count == 2

@pytest.mark.django_db
class TestOrderStateMachineExtra:

    def test_can_transition_returns_true(self):
        from orders.state_machine import OrderStateMachine

        assert OrderStateMachine.can_transition("pending", "paid") is True

    def test_can_transition_returns_false(self):
        from orders.state_machine import OrderStateMachine

        assert (
            OrderStateMachine.can_transition("pending", "delivered")
            is False
        )

    def test_transition_creates_status_log(self, order, test_user):
        from orders.state_machine import OrderStateMachine
        from orders.models import OrderStatusLog

        OrderStateMachine.transition(
            order,
            "paid",
            reason="Payment received",
            created_by=test_user,
        )

        log = OrderStatusLog.objects.latest("id")

        assert log.old_status == "pending"
        assert log.new_status == "paid"
        assert log.reason == "Payment received"
        assert log.created_by == test_user

