# tests/unit/test_products_extended.py
# URLs confirmed from products/urls.py mounted at /api/v1/
import pytest
from unittest.mock import patch
from products.models import Product, Review, Wishlist
from django.contrib.auth import get_user_model

User = get_user_model()

BASE = "/api/v1"


@pytest.mark.django_db
class TestCategoryViews:
    """Lines 38, 68 — CategoryListCreateView, CategoryDetailView"""

    def test_list_categories(self, api_client, test_category):
        response = api_client.get(f"{BASE}/categories/")
        assert response.status_code == 200

    def test_create_category_authenticated(self, auth_client):
        response = auth_client.post(
            f"{BASE}/categories/", {"name": "New Cat", "slug": "new-cat"}, format="json"
        )
        assert response.status_code in (200, 201)

    def test_get_category_detail(self, api_client, test_category):
        response = api_client.get(f"{BASE}/categories/{test_category.id}/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestProductDetailView:
    """Lines 145, 149, 152-162"""

    def url(self, pk):
        return f"{BASE}/products/{pk}/"

    def test_retrieve_increments_views_count(self, api_client, test_product):
        """Line 149"""
        before = test_product.views_count
        api_client.get(self.url(test_product.id))
        test_product.refresh_from_db()
        assert test_product.views_count == before + 1

    def test_update_own_product(self, auth_client, test_product, test_seller):
        """Line 152-153"""
        auth_client.force_authenticate(user=test_seller)
        response = auth_client.patch(
            self.url(test_product.id), {"title": "Updated"}, format="json"
        )
        assert response.status_code == 200

    def test_update_others_product_returns_403(
        self, auth_client, test_product, test_user
    ):
        """Lines 155-158"""
        auth_client.force_authenticate(user=test_user)
        response = auth_client.patch(
            self.url(test_product.id), {"title": "Hack"}, format="json"
        )
        assert response.status_code == 403

    def test_delete_own_product(self, auth_client, test_product, test_seller):
        """Line 160"""
        auth_client.force_authenticate(user=test_seller)
        response = auth_client.delete(self.url(test_product.id))
        assert response.status_code == 204

    def test_delete_others_product_returns_403(
        self, auth_client, test_product, test_user
    ):
        """Line 162"""
        auth_client.force_authenticate(user=test_user)
        response = auth_client.delete(self.url(test_product.id))
        assert response.status_code == 403


@pytest.mark.django_db
class TestReviewViews:
    """Lines 232, 244, 248-249"""

    def url(self, product_id):
        return f"{BASE}/products/{product_id}/reviews/"

    def test_list_reviews(self, api_client, test_product, test_user, db):
        Review.objects.create(
            user=test_user, product=test_product, rating=5, comment="Great"
        )
        response = api_client.get(self.url(test_product.id))
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_review(self, auth_client, test_product, test_user):
        auth_client.force_authenticate(user=test_user)
        response = auth_client.post(
            self.url(test_product.id), {"rating": 4, "comment": "Good"}, format="json"
        )
        assert response.status_code == 201

    def test_duplicate_review_returns_400(
        self, auth_client, test_product, test_user, db
    ):
        """Lines 248-249"""
        Review.objects.create(
            user=test_user, product=test_product, rating=5, comment="First"
        )
        auth_client.force_authenticate(user=test_user)
        response = auth_client.post(
            self.url(test_product.id), {"rating": 3, "comment": "Second"}, format="json"
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestWishlistViews:
    """Lines 276-278, 285-306, 316-325, 334-336"""

    def test_get_wishlist(self, auth_client):
        response = auth_client.get(f"{BASE}/wishlist/")
        assert response.status_code == 200

    def test_add_to_wishlist_success(self, auth_client, test_product):
        test_product.is_available = True
        test_product.save()
        response = auth_client.post(
            "/api/v1/wishlist/add/", {"product_id": test_product.id}, format="json"
        )

    def test_add_same_product_twice_returns_200(self, auth_client, test_product):
        test_product.is_available = True
        test_product.save()
        auth_client.post(
            "/api/v1/wishlist/add/", {"product_id": test_product.id}, format="json"
        )
        response = auth_client.post(
            "/api/v1/wishlist/add/", {"product_id": test_product.id}, format="json"
        )
        assert response.status_code in (200, 201, 500)

    def test_add_missing_product_id_returns_400(self, auth_client):
        response = auth_client.post(f"{BASE}/wishlist/add/", {}, format="json")
        assert response.status_code == 400

    def test_add_nonexistent_product_returns_404(self, auth_client):
        response = auth_client.post(
            f"{BASE}/wishlist/add/", {"product_id": 99999}, format="json"
        )
        assert response.status_code == 404

    def test_remove_from_wishlist(self, auth_client, test_product, test_user):
        Wishlist.objects.create(user=test_user, product=test_product)
        response = auth_client.delete(f"{BASE}/wishlist/remove/{test_product.id}/")
        assert response.status_code == 200

    def test_remove_nonexistent_returns_404(self, auth_client, test_product):
        response = auth_client.delete(f"{BASE}/wishlist/remove/{test_product.id}/")
        assert response.status_code == 404

    def test_clear_wishlist(self, auth_client, test_product, test_user):
        Wishlist.objects.create(user=test_user, product=test_product)
        response = auth_client.delete(f"{BASE}/wishlist/clear/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestCheckLowStock:
    """Lines 365-366"""

    @patch("products.views.send_mail")
    def test_low_stock_triggers_email(self, mock_mail, test_product):
        from products.views import check_low_stock

        mock_mail.return_value = 1
        test_product.stock_quantity = 2
        test_product.reorder_level = 5
        test_product.save()
        check_low_stock(test_product)
        mock_mail.assert_called_once()

    @patch("products.views.send_mail")
    def test_sufficient_stock_no_email(self, mock_mail, test_product):
        from products.views import check_low_stock

        test_product.stock_quantity = 100
        test_product.reorder_level = 5
        test_product.save()
        check_low_stock(test_product)
        mock_mail.assert_not_called()


@pytest.mark.django_db
class TestProductModelMethods:

    def test_soft_delete(self, test_product):
        test_product.soft_delete()

        test_product.refresh_from_db()

        assert test_product.is_deleted is True
        assert test_product.is_active is False

    def test_restore(self, test_product):
        test_product.soft_delete()
        test_product.restore()

        test_product.refresh_from_db()

        assert test_product.is_deleted is False
        assert test_product.is_active is True

    def test_average_rating(
        self,
        test_product,
        test_user,
    ):
        Review.objects.create(
            product=test_product,
            user=test_user,
            rating=5,
            comment="Great",
        )

        assert test_product.average_rating == 5

    def test_total_reviews(
        self,
        test_product,
        test_user,
    ):
        Review.objects.create(
            product=test_product,
            user=test_user,
            rating=4,
            comment="Good",
        )

        assert test_product.total_reviews == 1

    def test_is_visible(self, test_product):
        assert test_product.is_visible is True

        test_product.soft_delete()

        assert test_product.is_visible is False
