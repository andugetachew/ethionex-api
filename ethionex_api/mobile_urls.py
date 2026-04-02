from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Mobile optimized endpoints
    path("mobile/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("mobile/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
