from django.contrib import admin
from django.urls import path, include

from dashboard_accessapp.apis.views import authentication


urlpatterns = [
    path("/login", authentication.AdminLoginView.as_view()),

]
