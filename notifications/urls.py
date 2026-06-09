from django.urls import path
from . import views

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notifications"),
    path(
        "<int:notification_id>/mark-read/",
        views.NotificationMarkReadView.as_view(),
        name="mark-read",
    ),
    path(
        "mark-all-read/",
        views.NotificationMarkAllReadView.as_view(),
        name="mark-all-read",
    ),
]
