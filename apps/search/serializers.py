from rest_framework import serializers
from apps.products.models import Product


class ProductSearchSerializer(serializers.ModelSerializer):
    """Serializer for product search results."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    quantity_in_store = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ('id', 'title', 'description', 'price', 'category_name', 'quantity_in_store', 'created_at')
        read_only_fields = fields
    
    def get_quantity_in_store(self, obj):
        """Get quantity for specific store if context provides store_id."""
        store_id = self.context.get('store_id')
        if not store_id:
            return None
        
        from apps.orders.models import Inventory
        try:
            inventory = Inventory.objects.get(product=obj, store_id=store_id)
            return inventory.quantity
        except Inventory.DoesNotExist:
            return 0


class SuggestSerializer(serializers.Serializer):
    """Serializer for autocomplete suggestions."""
    title = serializers.CharField(read_only=True)
    id = serializers.IntegerField(read_only=True)
