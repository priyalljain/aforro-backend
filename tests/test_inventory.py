from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.products.models import Category, Product
from apps.stores.models import Store
from apps.orders.models import Inventory


class InventoryManagementTestCase(APITestCase):
    """Test inventory management and edge cases."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.category = Category.objects.create(name='Electronics')
        self.store = Store.objects.create(name='Tech Store', location='NYC')
        
        # Create products
        self.product1 = Product.objects.create(
            title='Laptop',
            price=999.99,
            category=self.category
        )
        self.product2 = Product.objects.create(
            title='Mouse',
            price=29.99,
            category=self.category
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
            quantity=50
        )
    
    def test_unique_together_constraint(self):
        """Test that store-product combination is unique."""
        with self.assertRaises(Exception):
            Inventory.objects.create(
                store=self.store,
                product=self.product1,
                quantity=10
            )
    
    def test_inventory_quantity_minimum_zero(self):
        """Test that inventory quantity cannot be negative."""
        inventory = Inventory(
            store=self.store,
            product=self.product2,
            quantity=-1
        )
        
        # Validation should catch this
        from django.core.exceptions import ValidationError
        with self.assertRaises((ValidationError, ValueError)):
            inventory.full_clean()
    
    def test_insufficient_stock_method(self):
        """Test has_sufficient_stock method."""
        self.assertTrue(self.inventory1.has_sufficient_stock(5))
        self.assertTrue(self.inventory1.has_sufficient_stock(3))
        self.assertFalse(self.inventory1.has_sufficient_stock(6))
    
    def test_deduct_stock_method(self):
        """Test deduct_stock method."""
        self.inventory1.deduct_stock(2)
        self.assertEqual(self.inventory1.quantity, 3)
    
    def test_deduct_stock_insufficient(self):
        """Test deduct_stock raises error when insufficient."""
        with self.assertRaises(ValueError):
            self.inventory1.deduct_stock(10)
    
    def test_inventory_zero_quantity(self):
        """Test inventory item with zero quantity."""
        inventory = Inventory.objects.create(
            store=Store.objects.create(name='Store 2', location='LA'),
            product=self.product1,
            quantity=0
        )
        
        self.assertFalse(inventory.has_sufficient_stock(1))
        self.assertTrue(inventory.has_sufficient_stock(0))
    
    def test_multiple_stores_same_product(self):
        """Test that same product can be in multiple stores."""
        store2 = Store.objects.create(name='Store 2', location='LA')
        inventory = Inventory.objects.create(
            store=store2,
            product=self.product1,
            quantity=20
        )
        
        self.assertEqual(
            Inventory.objects.filter(product=self.product1).count(),
            2
        )
