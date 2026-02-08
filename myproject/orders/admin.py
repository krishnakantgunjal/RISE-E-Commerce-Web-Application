from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Order, OrderItem
import csv

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status',
        'paid',
        'paid_at',
        'shipped_at',
        'delivered_at',
        'get_total_price',
        'created_at',
    )

    list_filter = ('paid', 'created_at')
    search_fields = ('id', 'user__username')
    readonly_fields = (
        'paid_at',
        'shipped_at',
        'delivered_at',
        'created_at',
        'updated_at',
        'get_total_price',
    )
    
    inlines = [OrderItemInline]

    def get_total_price(self, obj):
        return obj.total_price()

    get_total_price.short_description = 'Total Price'

    def status(self, obj):
        return "Paid ✅" if obj.paid else "Pending ❌"
    
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
