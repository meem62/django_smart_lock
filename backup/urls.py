# project_name/urls.py

from django.contrib import admin
from django.urls import path, include  # Ensure 'include' is imported

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('smartdoor.urls')),  # Correctly include the smartdoor app's URLs
]
