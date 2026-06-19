from django.db import models
from django.core.validators import MinValueValidator
from apps.products.models import Product
from apps.stores.models import Store


class Inventory(models.Model):
    """Stock tracking for products in stores."""
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='inventory',
        help_text="Store that holds this inventory"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory',
        help_text="Product in inventory"
    )
    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current stock quantity"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventory"
        unique_together = ('store', 'product')
        ordering = ['store', 'product']
        indexes = [
            models.Index(fields=['store', 'product']),
            models.Index(fields=['store']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.store.name} - {self.product.title}: {self.quantity} units"

    def has_sufficient_stock(self, quantity_requested):
        """Check if sufficient stock is available."""
        return self.quantity >= quantity_requested

    def deduct_stock(self, quantity):
        """Safely deduct stock quantity."""
        if self.quantity < quantity:
            raise ValueError(f"Insufficient stock. Available: {self.quantity}, Requested: {quantity}")
        self.quantity -= quantity
        self.save(update_fields=['quantity', 'updated_at'])


class Order(models.Model):
    """Customer orders with status tracking."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
    ]

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='orders',
        help_text="Store processing this order"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True,
        help_text="Current order status"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.store.name} ({self.status})"

    def get_total_items(self):
        """Get total number of items in this order."""
        return sum(item.quantity_requested for item in self.items.all())

    def get_order_items_cost(self):
        """Calculate total cost of the order."""
        total = sum(
            item.product.price * item.quantity_requested
            for item in self.items.all()
        )
        return total


class OrderItem(models.Model):
    """Individual items within an order."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Parent order"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        help_text="Ordered product"
    )
    quantity_requested = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity requested in this order"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Order Items"
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.product.title} x {self.quantity_requested} (Order #{self.order.id})"
