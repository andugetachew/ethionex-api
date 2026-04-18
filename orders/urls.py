from django.urls import path
from . import views

urlpatterns = [
    path("", views.OrderListCreateView.as_view(), name="orders"),
    path(
        "<str:order_number>/", views.OrderDetailView.as_view(), name="order-detail"
    ),  # Change int to str
]
