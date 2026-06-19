from django.test import TestCase
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.products.models import Category, Product
from apps.stores.models import Store
from apps.orders.models import Order, OrderItem, Inventory
import json
import random


class OrderCreationTestCase(APITestCase):
    """Test order creation with transaction isolation and inventory validation."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test category
        self.category = Category.objects.create(name='Electronics')
        
        # Create test products
        self.product1 = Product.objects.create(
            title='Laptop',
            description='High-performance laptop',
            price=999.99,
            category=self.category
        )
        self.product2 = Product.objects.create(
            title='Mouse',
            description='Wireless mouse',
            price=29.99,
            category=self.category
        )
        
        # Create test store
        self.store = Store.objects.create(
            name='TechStore',
            location='New York'
        )
        
        # Create inventory
        self.inventory1 = Inventory.objects.create(
            store=self.store,
            product=self.product1,
            quantity=5
        )
        self.inventory2 = Inventory.objects.create(
            store=self.store,
            product=self.product2,
            quantity=100
        )
    
    def test_order_creation_with_sufficient_stock(self):
        """Test successful order creation when stock is available."""
        payload = {
            'store_id': self.store.id,
            'items': [
                {'product_id': self.product1.id, 'quantity_requested': 2},
                {'product_id': self.product2.id, 'quantity_requested': 10}
            ]
        }
        
        response = self.client.post('/api/orders/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'CONFIRMED')
        self.assertEqual(response.data['total_items'], 12)
        
        # Verify stock was deducted
        self.inventory1.refresh_from_db()
        self.inventory2.refresh_from_db()
        self.assertEqual(self.inventory1.quantity, 3)
        self.assertEqual(self.inventory2.quantity, 90)
    
    def test_order_creation_with_insufficient_stock(self):
        """Test order creation is REJECTED when stock is insufficient."""
        payload = {
            'store_id': self.store.id,
            'items': [
                {'product_id': self.product1.id, 'quantity_requested': 10}  # Only 5 available
            ]
        }
        
        response = self.client.post('/api/orders/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'REJECTED')
        
        # Verify stock was NOT deducted
        self.inventory1.refresh_from_db()
        self.assertEqual(self.inventory1.quantity, 5)
    
    def test_order_creation_partial_insufficient_stock(self):
        """Test order is REJECTED if any item has insufficient stock."""
        payload = {
            'store_id': self.store.id,
            'items': [
                {'product_id': self.product1.id, 'quantity_requested': 2},  # Available
                {'product_id': self.product2.id, 'quantity_requested': 200}  # Not available
            ]
        }
        
        response = self.client.post('/api/orders/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'REJECTED')
        
        # Verify NO stock was deducted
        self.inventory1.refresh_from_db()
        self.inventory2.refresh_from_db()
        self.assertEqual(self.inventory1.quantity, 5)
        self.assertEqual(self.inventory2.quantity, 100)
    
    def test_order_contains_order_items(self):
        """Test that created order contains proper order items."""
        payload = {
            'store_id': self.store.id,
            'items': [
                {'product_id': self.product1.id, 'quantity_requested': 2},
            ]
        }
        
        response = self.client.post('/api/orders/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['items']), 1)
        
        item = response.data['items'][0]
        self.assertEqual(item['product'], self.product1.id)
        self.assertEqual(item['quantity_requested'], 2)
    
    def test_duplicate_products_in_order(self):
        """Test that duplicate products in single order are rejected."""
        payload = {
            'store_id': self.store.id,
            'items': [
                {'product_id': self.product1.id, 'quantity_requested': 2},
                {'product_id': self.product1.id, 'quantity_requested': 1},  # Duplicate
            ]
        }
        
        response = self.client.post('/api/orders/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderListingTestCase(APITestCase):
    """Test order listing endpoint with N+1 query prevention."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            title='Laptop',
            price=999.99,
            category=self.category
        )
        self.store = Store.objects.create(name='TechStore', location='NYC')
        
        # Create multiple orders
        for i in range(5):
            order = Order.objects.create(store=self.store, status='CONFIRMED')
            OrderItem.objects.create(
                order=order,
                product=self.product,
                quantity_requested=i + 1
            )
    
    def test_order_list_by_store(self):
        """Test listing orders for a specific store."""
        response = self.client.get(f'/api/orders/store/{self.store.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
    
    def test_order_list_n_plus_one_queries(self):
        """Test that order listing doesn't have N+1 query problem."""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(f'/api/orders/store/{self.store.id}/')
        
        # Should be minimal queries (not multiplied by number of orders)
        # Expected: 1 query for orders + 1 for items + 1 for pagination = ~3
        self.assertLess(len(context.captured_queries), 10)


class InventoryListingTestCase(APITestCase):
    """Test inventory listing with query optimization."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name='Electronics')
        
        # Create products
        self.products = [
            Product.objects.create(
                title=f'Product {i}',
                price=100 + i,
                category=self.category
            )
            for i in range(5)
        ]
        
        self.store = Store.objects.create(name='TechStore', location='NYC')
        
        # Create inventory
        for product in self.products:
            Inventory.objects.create(
                store=self.store,
                product=product,
                quantity=random.randint(10, 100)
            )
    
    def test_inventory_list_by_store(self):
        """Test listing inventory for a specific store."""
        response = self.client.get(f'/api/orders/inventory/store/{self.store.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
    
    def test_inventory_list_alphabetical_order(self):
        """Test that inventory is sorted alphabetically by product title."""
        response = self.client.get(f'/api/orders/inventory/store/{self.store.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        titles = [item['product_title'] for item in response.data]
        self.assertEqual(titles, sorted(titles))
    
    def test_inventory_list_contains_all_fields(self):
        """Test that inventory response contains all required fields."""
        response = self.client.get(f'/api/orders/inventory/store/{self.store.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        item = response.data[0]
        required_fields = ['product_title', 'product_price', 'category_name', 'quantity']
        for field in required_fields:
            self.assertIn(field, item)
    
    def test_inventory_select_related_queries(self):
        """Test that inventory listing uses select_related to prevent N+1."""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(f'/api/orders/inventory/store/{self.store.id}/')
        
        # Should use select_related - minimal queries
        self.assertLess(len(context.captured_queries), 5)
