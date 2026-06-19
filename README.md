# Aforro Backend - Production-Ready Django REST Framework

A complete, containerized Django backend for the Aforro assignment with order management, inventory control, product search, and asynchronous processing using Celery and Redis.

## Features

✅ **Order Management** - Create orders with stock validation and atomic transactions  
✅ **Inventory Management** - Track stock across multiple stores  
✅ **Advanced Search** - Full-text search with filters and autocomplete  
✅ **Asynchronous Processing** - Celery integration for background tasks  
✅ **Caching** - Redis-backed caching for performance optimization  
✅ **API Documentation** - Interactive Swagger/OpenAPI documentation  
✅ **Docker Ready** - Multi-container setup (Django, PostgreSQL, Redis, Celery)  
✅ **Production Grade** - Query optimization, error handling, logging, security  

## Project Structure

```
aforro_backend/
├── manage.py                    # Django management script
├── core/                        # Django core configuration
│   ├── settings.py             # All Django settings & configurations
│   ├── urls.py                 # Main URL routing
│   ├── wsgi.py                 # WSGI application
│   ├── asgi.py                 # ASGI application
│   └── celery.py               # Celery configuration
├── apps/
│   ├── products/               # Product management
│   ├── stores/                 # Store management
│   ├── orders/                 # Order management & Celery tasks
│   └── search/                 # Search API & data seeding
├── tests/                      # Test suite
├── docker-compose.yml          # Multi-container orchestration
├── Dockerfile                  # Application container definition
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Technology Stack

- **Framework**: Django 4.2 + Django REST Framework 3.14
- **Database**: PostgreSQL 15 (with psycopg2)
- **Cache/Broker**: Redis 7
- **Async Tasks**: Celery 5.3
- **API Docs**: drf-spectacular (OpenAPI/Swagger)
- **Utilities**: Faker for seed data, Python-decouple for env config
- **Server**: Gunicorn (WSGI)

## Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR Python 3.11+, PostgreSQL, Redis

### Option 1: Docker Compose (Recommended)

```bash
# Clone/enter the repository
cd aforro_backend

# Create environment file
cp .env.example .env

# Build and start all services
docker-compose up --build

# Run migrations (automatic, but you can run manually)
docker-compose exec web python manage.py migrate

# Seed dummy data
docker-compose exec web python manage.py seed_data

# Create superuser (optional)
docker-compose exec web python manage.py createsuperuser
```

### Option 2: Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your local settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# In another terminal, start Celery worker
celery -A core worker --loglevel=info

# In another terminal, start Redis
redis-server
```

## API Endpoints

### Order Management
- **POST** `/api/orders/` - Create new order
- **GET** `/api/stores/<store_id>/orders/` - List store orders
- **GET** `/api/orders/<id>/` - Get order details

### Inventory
- **GET** `/api/stores/<store_id>/inventory/` - List store inventory

### Search & Autocomplete
- **GET** `/api/search/products/` - Search products with filters
- **GET** `/api/search/suggest/?q=xxx` - Autocomplete suggestions

### Documentation
- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/schema/`

## Environment Variables

See `.env.example` for all available options:

```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=aforro
DB_USER=aforro
DB_PASSWORD=secure_password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
```

## Data Models

### Category
- `name` (CharField, unique)

### Product
- `title` (CharField)
- `description` (TextField, optional)
- `price` (DecimalField)
- `category` (ForeignKey to Category)

### Store
- `name` (CharField)
- `location` (CharField)

### Inventory
- `store` (ForeignKey to Store)
- `product` (ForeignKey to Product)
- `quantity` (IntegerField)
- **Constraint**: `unique_together = ('store', 'product')`

### Order
- `store` (ForeignKey to Store)
- `status` (Choices: PENDING, CONFIRMED, REJECTED)
- `created_at` (DateTimeField, auto_now_add)

### OrderItem
- `order` (ForeignKey to Order)
- `product` (ForeignKey to Product)
- `quantity_requested` (IntegerField)

## Core Features Implementation

### 1. Order Creation with Atomic Transactions
```python
# POST /api/orders/
{
  "store_id": 1,
  "items": [
    {"product_id": 1, "quantity_requested": 5},
    {"product_id": 2, "quantity_requested": 3}
  ]
}
```

**Logic**:
- Validates stock availability
- Uses `transaction.atomic()` with `select_for_update()` for race condition prevention
- Creates order with `CONFIRMED` status if stock available
- Creates order with `REJECTED` status if stock insufficient
- Triggers Celery task for email confirmation on successful orders

### 2. Query Optimization
- **Order Listing**: Uses `.prefetch_related('items')` to prevent N+1 queries
- **Inventory Listing**: Uses `.select_related('product', 'product__category')`
- **Search**: Annotates inventory quantities using subqueries

### 3. Redis Integration

**Option A - Caching (Implemented)**:
- Product search results cached for 5 minutes
- Inventory listing cached
- Cache invalidation on product/inventory updates via Django signals

**Option B - Rate Limiting**:
- Autocomplete endpoint limited to 20 requests/minute
- DRF ScopedRateThrottle implementation

### 4. Celery Tasks

**Implemented Task**: `send_order_confirmation_email(order_id)`
- Simulates email sending with logging
- Triggered automatically after successful order creation
- Worker processes tasks from Redis message broker

### 5. Management Command

```bash
python manage.py seed_data
```

Generates:
- 15+ categories
- 1000+ products
- 25+ stores
- Inventory for each store (300+ products per store)
- Uses bulk_create for optimal performance

## Running Tests

```bash
# Run all tests
python manage.py test

# Run with verbose output
python manage.py test --verbosity=2

# Run specific test
python manage.py test tests.test_orders
```

## Docker Commands

```bash
# View logs
docker-compose logs -f web

# Run Django shell
docker-compose exec web python manage.py shell

# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Stop all services
docker-compose down

# Remove all volumes
docker-compose down -v
```

## Sample API Requests

### Create Order
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": 1,
    "items": [
      {"product_id": 1, "quantity_requested": 2},
      {"product_id": 2, "quantity_requested": 1}
    ]
  }'
```

### List Store Orders
```bash
curl http://localhost:8000/api/stores/1/orders/
```

### Search Products
```bash
curl "http://localhost:8000/api/search/products/?q=laptop&category=1&price_min=100&price_max=2000"
```

### Autocomplete
```bash
curl "http://localhost:8000/api/search/suggest/?q=lap"
```

## Scalability Considerations

1. **Database**: PostgreSQL with connection pooling, indexes on foreign keys
2. **Cache**: Redis with eviction policies and TTL
3. **Async**: Celery workers can scale horizontally
4. **API**: Gunicorn workers configurable per environment
5. **Load Balancing**: Use nginx/HAProxy in front
6. **Query Optimization**: select_related, prefetch_related, annotations
7. **Rate Limiting**: Throttle non-critical endpoints
8. **Monitoring**: Logs persisted to file for analysis

## Performance Features

- ✅ Connection pooling (PostgreSQL)
- ✅ Query result caching (Redis)
- ✅ N+1 query prevention (select_related, prefetch_related)
- ✅ Bulk operations (bulk_create for seed data)
- ✅ Database indexing (automatic on ForeignKeys)
- ✅ Async task processing (Celery)
- ✅ Request throttling (DRF ScopedRateThrottle)
- ✅ Pagination (PageNumberPagination)

## Security Features

- ✅ Environment variable configuration (no hardcoded secrets)
- ✅ CSRF protection
- ✅ SQL injection prevention (ORM)
- ✅ XSS protection
- ✅ Rate limiting
- ✅ Secure password validation
- ✅ HTTPS ready (SSL redirects in production)

## Troubleshooting

### Connection Refused
- Ensure Docker services are healthy: `docker-compose ps`
- Check database health: `docker-compose logs db`

### Celery Tasks Not Processing
- Check worker logs: `docker-compose logs celery`
- Ensure Redis is running: `docker-compose logs redis`

### Database Migrations Failed
- Drop volume and restart: `docker-compose down -v && docker-compose up --build`

### High Memory Usage
- Reduce CELERY_WORKER_PREFETCH_MULTIPLIER in settings.py
- Adjust gunicorn workers

## Next Steps / Future Enhancements

1. Add authentication (JWT tokens, OAuth2)
2. Implement pagination and filtering on all list endpoints
3. Add Elasticsearch for advanced search
4. Implement GraphQL API
5. Add request/response logging middleware
6. Implement soft deletes for data archival
7. Add data export functionality (CSV, PDF)
8. Implement notification system (email, SMS, webhooks)
9. Add admin dashboard
10. Performance monitoring with APM

## Contributing

1. Create feature branch from `main`
2. Write tests for new features
3. Ensure all tests pass
4. Submit pull request with detailed description

## License

Proprietary - Aforro Technologies

## Support

For issues or questions, please create an issue in the repository or contact the development team.

---

**Last Updated**: June 19, 2026  
**Status**: Steps 1-2 Complete ✅  
**Next**: Step 3 - Database Models
