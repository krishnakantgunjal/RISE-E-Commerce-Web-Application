from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Order, OrderItem
import csv

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity', 'get_subtotal')
    can_delete = False

    def get_subtotal(self, obj):
        return obj.get_total_price()
    get_subtotal.short_description = 'Subtotal'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status_badge',
        'paid',
        'get_total_price',
        'created_at',
    )

    list_filter = ('paid', 'status', 'created_at')
    search_fields = ('id', 'user__username', 'email')
    
    readonly_fields = (
        'user',
        'get_total_price',
        'paid_at',
        'shipped_at',
        'delivered_at',
        'created_at',
        'updated_at',
    )
    
    inlines = [OrderItemInline]
    
    actions = ['mark_as_paid']

    def get_total_price(self, obj):
        return obj.total_price()
    get_total_price.short_description = 'Total Price'
    get_total_price.admin_order_field = 'total_amount' # Assumes total_amount is stored in DB for sorting

    def status_badge(self, obj):
        color = "orange"
        if obj.status == "delivered":
             color = "green"
        elif obj.status == "shipped":
             color = "blue"
        elif obj.status == "cancelled":
             color = "red"
        elif obj.status == "processing":
             color = "purple"
             
        return format_html(
            '<strong style="color:{};">{}</strong>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
    
    @admin.action(description="Mark selected orders as Paid")
    def mark_as_paid(self, request, queryset):
        # Use timezone.now() for timezone-aware datetimes
        from django.utils import timezone
        updated = queryset.update(paid=True, payment_status='completed', paid_at=timezone.now())
        self.message_user(request, f"{updated} orders marked as paid.", messages.SUCCESS)

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'product',
        'price',
        'quantity',
        'get_subtotal',
    )

    search_fields = ('order__id', 'product__name')

    def get_subtotal(self, obj):
        return obj.get_total_price()

    get_subtotal.short_description = 'Subtotal'


# Customize admin site headers
admin.site.site_header = "RISE E-Commerce Admin"
admin.site.site_title = "RISE Admin Portal"
admin.site.index_title = "Order Management System"
