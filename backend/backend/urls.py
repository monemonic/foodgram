from django.contrib import admin
from django.urls import path, include

from api.v1.utils import SearchRedirectView


urlpatterns = [
    path('s/<int:pk>/', SearchRedirectView.as_view()),
    path('admin/', admin.site.urls),
    path('api/', include('api.v1.urls')),
]
