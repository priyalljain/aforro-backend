from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('products/', views.search_products, name='search-products'),
    path('suggest/', views.search_suggest, name='search-suggest'),
]
