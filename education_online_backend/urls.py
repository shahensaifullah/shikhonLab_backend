from django.contrib import admin
from django.urls import path, include
from pictures.conf import get_settings

urlpatterns = [
    path("admin/", admin.site.urls),
    # rest framework
    path("api-auth/", include("rest_framework.urls")),
]

if get_settings().USE_PLACEHOLDERS:
    urlpatterns += [
        path("_pictures/", include("pictures.urls")),
    ]
