from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'orders'

router = DefaultRouter()
router.register(r'', views.OrderViewSet, basename='order')
router.register(r'inventory', views.InventoryViewSet, basename='inventory')

urlpatterns = [
    path('', include(router.urls)),
]
