from rest_framework import viewsets
from .models import Store
from .serializers import StoreSerializer


class StoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stores.
    Supports CRUD operations on store records.
    """
    queryset = Store.objects.all().order_by('name')
    serializer_class = StoreSerializer
    filterset_fields = ['name']
    search_fields = ['name', 'location']
    ordering_fields = ['name', 'created_at']
