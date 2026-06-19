from django.contrib import admin
from .models import Inventory, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items."""
    model = OrderItem
    extra = 1
    fields = ('product', 'quantity_requested')
    readonly_fields = ('created_at',)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('store', 'product', 'quantity', 'updated_at')
    list_filter = ('store', 'product__category')
    search_fields = ('store__name', 'product__title')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Inventory Information', {
            'fields': ('store', 'product', 'quantity')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'store', 'status', 'get_total_items', 'created_at')
    list_filter = ('status', 'store', 'created_at')
    search_fields = ('store__name',)
    readonly_fields = ('created_at', 'updated_at', 'get_total_items', 'get_order_items_cost')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('store', 'status')
        }),
        ('Summary', {
            'fields': ('get_total_items', 'get_order_items_cost'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity_requested', 'created_at')
    list_filter = ('order__status', 'created_at')
    search_fields = ('order__id', 'product__title')
    readonly_fields = ('created_at',)
