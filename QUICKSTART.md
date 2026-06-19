# Quick Start Guide

## Local Development (No Docker)

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Seed Data
```bash
python manage.py seed_data
```

### 6. Start Development Server
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A core worker --loglevel=info

# Terminal 3: Redis (if not running as service)
redis-server
```

### 7. Access APIs
- Django Admin: http://localhost:8000/admin
- Swagger UI: http://localhost:8000/swagger/
- API Root: http://localhost:8000/api/

---

## Docker Deployment

### 1. Build & Start
```bash
cp .env.example .env
docker-compose up --build
```

### 2. Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 3. Seed Data
```bash
docker-compose exec web python manage.py seed_data
```

### 4. View Logs
```bash
docker-compose logs -f web
docker-compose logs -f celery
```

---

## Common Commands

### Django Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Django shell
python manage.py shell

# Run tests
python manage.py test

# Collect static files
python manage.py collectstatic
```

### Docker
```bash
# Stop services
docker-compose down

# Remove volumes
docker-compose down -v

# Rebuild
docker-compose build --no-cache

# View specific logs
docker-compose logs db
docker-compose logs redis
```

---

## API Examples

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
curl http://localhost:8000/api/orders/store/1/
```

### Search Products
```bash
curl "http://localhost:8000/api/search/products/?q=laptop&category=1&price_min=100&price_max=2000"
```

### Autocomplete
```bash
curl "http://localhost:8000/api/search/suggest/?q=lap&limit=10"
```

### Get Store Inventory
```bash
curl http://localhost:8000/api/orders/inventory/store/1/
```

---

## Running Tests

### All Tests
```bash
python manage.py test
```

### Specific Test File
```bash
python manage.py test tests.test_orders
python manage.py test tests.test_search
python manage.py test tests.test_inventory
```

### With Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

---

## Production Checklist

- [ ] Set DEBUG=False in .env
- [ ] Change SECRET_KEY to a secure value
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up SSL/TLS
- [ ] Configure email settings
- [ ] Use PostgreSQL (not SQLite)
- [ ] Configure Redis with authentication
- [ ] Set up monitoring/logging
- [ ] Configure backup strategy
- [ ] Load test the application

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

### Database Connection Refused
- Ensure PostgreSQL is running
- Check DB credentials in .env
- For Docker: `docker-compose logs db`

### Celery Tasks Not Processing
- Check Redis is running
- Verify CELERY_BROKER_URL is correct
- Check celery worker logs

### Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```

---

## Performance Tips

1. **Use Redis**: For caching and Celery
2. **Database Indexes**: Already configured on common fields
3. **Query Optimization**: Using select_related and prefetch_related
4. **Pagination**: Limit large result sets
5. **Rate Limiting**: Configure for public endpoints
6. **Connection Pooling**: Configured for PostgreSQL

---

## Further Reading

- [Django Docs](https://docs.djangoproject.com/)
- [DRF Docs](https://www.django-rest-framework.org/)
- [Celery Docs](https://docs.celeryproject.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Redis Docs](https://redis.io/documentation)
