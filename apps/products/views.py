from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product categories.
    """
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products.
    """
    queryset = Product.objects.all().select_related('category').order_by('-created_at')
    serializer_class = ProductSerializer
    
    # 1. Explicitly state the filter backends to ensure they apply in order
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # 2. Change this to a dictionary to enable specific lookups like __gte and __lte
    filterset_fields = {
        'category': ['exact'],
        'price': ['exact', 'gte', 'lte'],  # This fixes test_search_by_price_range
    }
    
    search_fields = ['title', 'description']
    
    # 3. This tells DRF it is allowed to sort the results by these fields
    ordering_fields = ['price', 'created_at', 'title']