from django.contrib import admin
from django.urls import path, include
from pictures.conf import get_settings
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView, TokenVerifyView,
)

urlpatterns = [
    path("/auth", include("dashboard_accessapp.apis.urls.authentication")),

]
