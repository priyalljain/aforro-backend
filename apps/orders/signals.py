from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

from apps.products.models import Product, Category
from .models import Inventory

logger = logging.getLogger(__name__)


def clear_related_caches():
    """Clear all related cache keys. Handles Redis connection errors gracefully."""
    cache_keys = [
        'aforro:products:search',
        'aforro:products:list',
        'aforro:inventory:list',
        'aforro:search:suggest',
    ]
    try:
        cache.delete_many(cache_keys)
    except Exception as e:
        # Log the error but don't crash if cache is unavailable
        logger.warning(f"Cache error during delete_many: {e}")


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """Invalidate search cache when product is updated/deleted."""
    clear_related_caches()


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """Invalidate cache when category is updated/deleted."""
    clear_related_caches()


@receiver(post_save, sender=Inventory)
@receiver(post_delete, sender=Inventory)
def invalidate_inventory_cache(sender, instance, **kwargs):
    """Invalidate cache when inventory is updated/deleted."""
    clear_related_caches()
