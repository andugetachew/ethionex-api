from django.urls import path
from . import views

urlpatterns = [
    path("", views.CartView.as_view(), name="cart"),
    path("add/", views.CartView.as_view(), name="add-to-cart"),
    path(
        "update/<int:item_id>/",
        views.UpdateCartItemView.as_view(),
        name="update-cart-item",
    ),
    path(
        "remove/<int:item_id>/",
        views.RemoveFromCartView.as_view(),
        name="remove-from-cart",
    ),
]
