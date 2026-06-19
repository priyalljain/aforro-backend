from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    class Meta:
        model = Category
        fields = ('id', 'name')


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with category details."""
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Product
        fields = ('id', 'title', 'description', 'price', 'category', 'category_id', 'created_at')
        read_only_fields = ('id', 'created_at')


class ProductDetailSerializer(ProductSerializer):
    """Detailed product serializer with additional metadata."""
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ('updated_at',)
        read_only_fields = ('id', 'created_at', 'updated_at')
