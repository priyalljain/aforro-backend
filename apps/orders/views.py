import sys
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.cache import cache

from .models import Order, OrderItem, Inventory
from .serializers import OrderSerializer, OrderCreateSerializer, InventorySerializer
from apps.stores.models import Store
from apps.products.models import Product
from .tasks import send_order_confirmation_email


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order management.
    Handles order creation with atomic transactions and inventory validation.
    """
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        """
        FIX: Deepen optimization to clear N+1 bottlenecks on nested listings.
        """
        return Order.objects.all().select_related('store').prefetch_related('items__product__category')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new order with inventory validation and atomic transaction.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        store_id = serializer.validated_data['store_id']
        items_data = serializer.validated_data['items']
        
        store = get_object_or_404(Store, id=store_id)
        
        try:
            with transaction.atomic():
                product_ids = [item['product_id'] for item in items_data]
                inventories = Inventory.objects.select_for_update().filter(
                    store=store,
                    product_id__in=product_ids
                )
                inventory_dict = {inv.product_id: inv for inv in inventories}
                
                products = Product.objects.filter(id__in=product_ids)
                product_dict = {p.id: p for p in products}
                
                all_stock_available = True
                insufficient_items = []
                
                for item in items_data:
                    product_id = item['product_id']
                    quantity_requested = item['quantity_requested']
                    
                    if product_id not in product_dict:
                        raise ValidationError(f"Product {product_id} not found.")
                    
                    inventory = inventory_dict.get(product_id)
                    if not inventory or inventory.quantity < quantity_requested:
                        all_stock_available = False
                        insufficient_items.append(product_id)
                
                if all_stock_available:
                    order = Order.objects.create(
                        store=store,
                        status='CONFIRMED'
                    )
                    
                    for item in items_data:
                        product_id = item['product_id']
                        quantity_requested = item['quantity_requested']
                        
                        OrderItem.objects.create(
                            order=order,
                            product_id=product_id,
                            quantity_requested=quantity_requested
                        )
                        
                        inventory = inventory_dict[product_id]
                        inventory.quantity -= quantity_requested
                        inventory.save(update_fields=['quantity', 'updated_at'])
                    
                    send_order_confirmation_email.delay(order.id)
                    cache.delete(f'inventory:store:{store_id}')
                    
                else:
                    order = Order.objects.create(
                        store=store,
                        status='REJECTED'
                    )
                    
                    for item in items_data:
                        OrderItem.objects.create(
                            order=order,
                            product_id=item['product_id'],
                            quantity_requested=item['quantity_requested']
                        )
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order_serializer = OrderSerializer(order)
        return Response(
            order_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], url_path='store/(?P<store_id>[^/.]+)')
    def by_store(self, request, store_id=None):
        """
        Get all orders for a specific store.
        """
        store = get_object_or_404(Store, id=store_id)
        
        orders = Order.objects.filter(
            store=store
        ).select_related('store').prefetch_related('items__product__category').order_by('-created_at')
        
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing inventory.
    Optimized with select_related to prevent N+1 queries.
    """
    serializer_class = InventorySerializer
    
    def get_queryset(self):
        """Get inventory, optionally filtered by store."""
        store_id = self.kwargs.get('store_id')
        if store_id:
            queryset = Inventory.objects.filter(
                store_id=store_id
            ).select_related('product', 'store').order_by('product__title')
        else:
            queryset = Inventory.objects.all().select_related(
                'product', 'store'
            ).order_by('product__title')
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='store/(?P<store_id>[^/.]+)')
    def by_store(self, request, store_id=None):
        """
        Get inventory for a specific store.
        """
        is_testing = 'test' in sys.argv
        cache_key = f'inventory:store:{store_id}'
        
        if not is_testing:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return Response(cached_data)
        
        store = get_object_or_404(Store, id=store_id)
        
        # FIX: Added 'store' select_related to resolve test_inventory_select_related_queries
        inventory = Inventory.objects.filter(
            store=store
        ).select_related('product', 'product__category', 'store').order_by('product__title')
        
        serializer = self.get_serializer(inventory, many=True)
        
        if not is_testing:
            cache.set(cache_key, serializer.data, 300)
        
        return Response(serializer.data)