from django.contrib import admin
from django.urls import path, include
from pictures.conf import get_settings
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView, TokenVerifyView,
)

urlpatterns = [
    path("admin", admin.site.urls),
    # rest framework
    path("apis-auth", include("rest_framework.urls")),

    # admin panel login
    path("api/root-admin", include("dashboard_accessapp.apis.urls")),

    # jwt token
    path('api/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify', TokenVerifyView.as_view(), name='token_verify'),
]


if get_settings().USE_PLACEHOLDERS:
    urlpatterns += [
        path("_pictures/", include("pictures.urls")),
    ]
