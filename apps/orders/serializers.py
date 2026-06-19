from rest_framework import serializers
from decimal import Decimal
from .models import Inventory, Order, OrderItem
from apps.products.serializers import ProductSerializer
from apps.stores.serializers import StoreSerializer


class InventorySerializer(serializers.ModelSerializer):
    """Serializer for Inventory with product details."""
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    category_name = serializers.CharField(source='product.category.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    
    class Meta:
        model = Inventory
        fields = (
            'id',
            'store',
            'store_name',
            'product',
            'product_title',
            'product_price',
            'category_name',
            'quantity',
            'updated_at'
        )
        read_only_fields = ('id', 'updated_at')


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_title', 'product_price', 'quantity_requested')
        read_only_fields = ('id',)


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items."""
    product_id = serializers.IntegerField()
    quantity_requested = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""
    items = OrderItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    store_name = serializers.CharField(source='store.name', read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'store', 'store_name', 'status', 'total_items', 'items', 'created_at')
        read_only_fields = ('id', 'items', 'total_items', 'created_at')
    
    def get_total_items(self, obj):
        return obj.get_total_items()


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders with inventory validation."""
    store_id = serializers.IntegerField()
    items = OrderItemCreateSerializer(many=True, min_length=1)
    
    def validate_items(self, items):
        """Validate items have unique products."""
        product_ids = [item['product_id'] for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Duplicate products in order items."
            )
        return items
