from django.urls import path
from . import views

urlpatterns = [
    path("stats/", views.SellerDashboardView.as_view(), name="seller-stats"),
]
