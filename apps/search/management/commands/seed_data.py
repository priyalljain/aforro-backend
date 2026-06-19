from django.core.management.base import BaseCommand
from django.db import connection
from faker import Faker
import random
from apps.products.models import Category, Product
from apps.stores.models import Store
from apps.orders.models import Inventory


class Command(BaseCommand):
    help = 'Seed the database with dummy data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            type=int,
            default=15,
            help='Number of categories to create'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=1050,
            help='Number of products to create'
        )
        parser.add_argument(
            '--stores',
            type=int,
            default=25,
            help='Number of stores to create'
        )
        parser.add_argument(
            '--products-per-store',
            type=int,
            default=300,
            help='Minimum products per store in inventory'
        )
    
    def handle(self, *args, **options):
        faker = Faker()
        
        num_categories = options['categories']
        num_products = options['products']
        num_stores = options['stores']
        products_per_store = options['products_per_store']
        
        self.stdout.write(self.style.SUCCESS('🌱 Starting database seeding...'))
        
        # Clear existing data
        self.stdout.write('🗑️  Clearing existing data...')
        Inventory.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Store.objects.all().delete()
        
        # Create categories
        self.stdout.write(f'📂 Creating {num_categories} categories...')
        categories = []
        category_names = set()
        
        while len(categories) < num_categories:
            name = faker.word().capitalize() + ' ' + faker.word().capitalize()
            if name not in category_names:
                category_names.add(name)
                categories.append(Category(name=name))
        
        Category.objects.bulk_create(categories)
        categories = Category.objects.all()
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(categories)} categories'))
        
        # Create products
        self.stdout.write(f'🛍️  Creating {num_products} products...')
        products = []
        
        for i in range(num_products):
            category = random.choice(categories)
            product = Product(
                title=faker.catch_phrase(),
                description=faker.text(max_nb_chars=200),
                price=round(random.uniform(10, 5000), 2),
                category=category
            )
            products.append(product)
            
            if (i + 1) % 500 == 0:
                self.stdout.write(f'  Created {i + 1}/{num_products} products...')
        
        Product.objects.bulk_create(products)
        products = list(Product.objects.all())
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(products)} products'))
        
        # Create stores
        self.stdout.write(f'🏪 Creating {num_stores} stores...')
        stores = []
        store_names = set()
        
        while len(stores) < num_stores:
            name = faker.company()
            if name not in store_names:
                store_names.add(name)
                stores.append(Store(
                    name=name,
                    location=faker.address()
                ))
        
        Store.objects.bulk_create(stores)
        stores = Store.objects.all()
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(stores)} stores'))
        
        # Create inventory
        self.stdout.write(f'📦 Creating inventory for {num_stores} stores...')
        inventory_count = 0
        batch_size = 1000
        inventory_items = []
        
        for store in stores:
            # Randomly select products for this store (at least products_per_store)
            num_products_for_store = random.randint(products_per_store, len(products))
            store_products = random.sample(products, num_products_for_store)
            
            for product in store_products:
                inventory = Inventory(
                    store=store,
                    product=product,
                    quantity=random.randint(0, 500)
                )
                inventory_items.append(inventory)
                inventory_count += 1
                
                if len(inventory_items) >= batch_size:
                    Inventory.objects.bulk_create(
                        inventory_items,
                        ignore_conflicts=True
                    )
                    self.stdout.write(f'  Created {inventory_count} inventory items...')
                    inventory_items = []
        
        # Create remaining inventory items
        if inventory_items:
            Inventory.objects.bulk_create(
                inventory_items,
                ignore_conflicts=True
            )
        
        total_inventory = Inventory.objects.count()
        self.stdout.write(self.style.SUCCESS(f'✅ Created {total_inventory} inventory items'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n📊 Seeding Summary:'))
        self.stdout.write(f'  • Categories: {Category.objects.count()}')
        self.stdout.write(f'  • Products: {Product.objects.count()}')
        self.stdout.write(f'  • Stores: {Store.objects.count()}')
        self.stdout.write(f'  • Inventory Items: {Inventory.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n✨ Database seeding completed successfully!'))
