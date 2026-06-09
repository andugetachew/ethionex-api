from django.urls import path
from . import views

urlpatterns = [
    # Stats
    path("stats/", views.AdminStatsView.as_view(), name="admin-stats"),
    # Users
    path("users/", views.UserListView.as_view(), name="admin-users"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="admin-user-detail"),
    path(
        "users/<int:user_id>/block/",
        views.BlockUserView.as_view(),
        name="admin-block-user",
    ),
    path(
        "users/<int:user_id>/unblock/",
        views.UnblockUserView.as_view(),
        name="admin-unblock-user",
    ),
    # Reports
    path("reports/sales/", views.SalesReportView.as_view(), name="admin-sales-report"),
    path(
        "reports/top-products/",
        views.TopProductsView.as_view(),
        name="admin-top-products",
    ),
    path(
        "reports/top-sellers/", views.TopSellersView.as_view(), name="admin-top-sellers"
    ),
]
