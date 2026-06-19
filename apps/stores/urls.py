from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'stores'

router = DefaultRouter()
router.register(r'', views.StoreViewSet, basename='store')

urlpatterns = [
    path('', include(router.urls)),
]
