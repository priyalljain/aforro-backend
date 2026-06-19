from rest_framework import serializers
from .models import Store


class StoreSerializer(serializers.ModelSerializer):
    """Serializer for Store model."""
    
    class Meta:
        model = Store
        fields = ('id', 'name', 'location', 'created_at')
        read_only_fields = ('id', 'created_at')
