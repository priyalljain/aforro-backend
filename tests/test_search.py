from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.products.models import Category, Product
from apps.stores.models import Store
from apps.orders.models import Inventory


class SearchProductsTestCase(APITestCase):
    """Test product search functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create categories
        self.electronics = Category.objects.create(name='Electronics')
        self.books = Category.objects.create(name='Books')
        
        # Create products
        self.laptop = Product.objects.create(
            title='Gaming Laptop',
            description='High-performance gaming laptop',
            price=1499.99,
            category=self.electronics
        )
        self.mouse = Product.objects.create(
            title='Wireless Mouse',
            description='Ergonomic wireless mouse',
            price=49.99,
            category=self.electronics
        )
        self.book = Product.objects.create(
            title='Python Programming',
            description='Learn Python programming',
            price=49.99,
            category=self.books
        )
    
    def test_search_by_keyword(self):
        """Test searching products by keyword."""
        response = self.client.get('/api/search/products/?q=laptop')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Gaming Laptop')
    
    def test_search_by_category(self):
        """Test filtering products by category."""
        response = self.client.get(f'/api/search/products/?category={self.electronics.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_search_by_price_range(self):
        """Test filtering products by price range."""
        response = self.client.get('/api/search/products/?price_min=100&price_max=500')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Gaming Laptop')
    
    def test_search_sort_by_price(self):
        """Test sorting products by price."""
        response = self.client.get('/api/search/products/?sort=price')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [item['price'] for item in response.data['results']]
        self.assertEqual(prices, sorted(prices))
    
    def test_search_sort_by_price_descending(self):
        """Test sorting products by price descending."""
        response = self.client.get('/api/search/products/?sort=-price')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [item['price'] for item in response.data['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))
    
    def test_search_multi_field(self):
        """Test search across multiple fields."""
        response = self.client.get('/api/search/products/?q=programming')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Python Programming')
    
    def test_search_with_store_id(self):
        """Test search includes inventory quantity when store_id provided."""
        store = Store.objects.create(name='Tech Store', location='NYC')
        Inventory.objects.create(store=store, product=self.laptop, quantity=5)
        
        response = self.client.get(f'/api/search/products/?store_id={store.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        laptop_result = next(
            (item for item in response.data['results'] if item['id'] == self.laptop.id),
            None
        )
        self.assertIsNotNone(laptop_result)
        self.assertEqual(laptop_result['quantity_in_store'], 5)


class SearchAutocompleteTestCase(APITestCase):
    """Test product autocomplete/suggest functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.category = Category.objects.create(name='Products')
        
        # Create products with specific names for testing
        self.laptop_pro = Product.objects.create(
            title='Laptop Pro',
            price=1999.99,
            category=self.category
        )
        self.laptop_basic = Product.objects.create(
            title='Laptop Basic',
            price=799.99,
            category=self.category
        )
        self.laptops_for_gaming = Product.objects.create(
            title='Laptops For Gaming',
            price=1499.99,
            category=self.category
        )
        self.mouse = Product.objects.create(
            title='Mouse Wireless',
            price=49.99,
            category=self.category
        )
    
    def test_suggest_minimum_query_length(self):
        """Test that suggest requires minimum 3 characters."""
        response = self.client.get('/api/search/suggest/?q=la')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_suggest_prefix_matching_first(self):
        """Test that products starting with query appear first."""
        response = self.client.get('/api/search/suggest/?q=laptop')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
        
        # All results should start with 'laptop' (case-insensitive)
        titles = [item['title'].lower() for item in response.data['results']]
        for title in titles:
            self.assertTrue(title.startswith('laptop'))
    
    def test_suggest_respects_limit(self):
        """Test that suggest respects the limit parameter."""
        response = self.client.get('/api/search/suggest/?q=laptop&limit=2')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(response.data['count'], 2)
    
    def test_suggest_limit_max_20(self):
        """Test that suggest maximum limit is 20."""
        response = self.client.get('/api/search/suggest/?q=laptop&limit=50')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(response.data['count'], 20)
    
    def test_suggest_default_limit_10(self):
        """Test that suggest defaults to 10 results."""
        # Create many products starting with 'laptop'
        for i in range(15):
            Product.objects.create(
                title=f'Laptop Model {i}',
                price=100 + i,
                category=self.category
            )
        
        response = self.client.get('/api/search/suggest/?q=laptop')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(response.data['count'], 10)
    
    def test_suggest_returns_id_and_title(self):
        """Test that suggest returns id and title fields."""
        response = self.client.get('/api/search/suggest/?q=laptop')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data['count'] > 0:
            result = response.data['results'][0]
            self.assertIn('id', result)
            self.assertIn('title', result)
    
    def test_suggest_case_insensitive(self):
        """Test that suggest is case-insensitive."""
        response = self.client.get('/api/search/suggest/?q=LAPTOP')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
