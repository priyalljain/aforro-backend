"""
Main URL configuration for Aforro backend project.
Routes all API endpoints and documentation.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Spectacular Schema Configuration
schema_view = SpectacularAPIView.as_view()

# Swagger/OpenAPI Documentation Views
swagger_view = SpectacularSwaggerView.as_view(url_name='schema')
redoc_view = SpectacularRedocView.as_view(url_name='schema')

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Routes
    path('api/orders/', include('apps.orders.urls')),
    path('api/stores/', include('apps.stores.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/search/', include('apps.search.urls')),
    
    # API Authentication
    path('api-auth/', include('rest_framework.urls')),
]
