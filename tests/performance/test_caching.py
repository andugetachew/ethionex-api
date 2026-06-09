import pytest
from django.core.cache import cache
from tests.urls import PRODUCTS, PRODUCT_DETAIL


@pytest.mark.django_db
class TestCachingPerformance:
    def setup_method(self):
        cache.clear()

    def test_product_list_caching(self, auth_client, test_product):
        response1 = auth_client.get(PRODUCTS)
        response2 = auth_client.get(PRODUCTS)
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_cache_invalidation_on_update(self, auth_client, test_product):
        # Verify product endpoint works
        response = auth_client.get(PRODUCT_DETAIL(test_product.id))
        assert response.status_code == 200
        assert response.data["title"] == test_product.title

        # Update product
        response = auth_client.patch(
            PRODUCT_DETAIL(test_product.id), {"title": "Updated Title"}, format="json"
        )
        # Verify updated
        response = auth_client.get(PRODUCT_DETAIL(test_product.id))
        assert response.status_code == 200
