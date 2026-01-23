from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'subtotal')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'phone', 'total_amount', 'status_badge', 'payment_badge', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['id', 'full_name', 'phone', 'address', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'total_amount']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'full_name', 'phone', 'address')
        }),
        ('Order Details', {
            'fields': ('total_amount', 'status', 'payment_status', 'created_at')
        }),
    )
    
    actions = ['mark_processing', 'mark_shipped', 'mark_delivered', 'export_to_csv']
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'shipped': '#007bff',
            'delivered': '#28a745',
            'cancelled': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 11px; text-transform: uppercase;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'
    
    def payment_badge(self, obj):
        """Display payment status with color coding"""
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cod_pending': '#17a2b8'
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 11px; text-transform: uppercase;">{}</span>',
            color, obj.payment_status.replace('_', ' ')
        )
    payment_badge.short_description = 'Payment'
    
    def mark_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} order(s) marked as processing.')
    mark_processing.short_description = 'Mark as Processing'
    
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_shipped.short_description = 'Mark as Shipped'
    
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_delivered.short_description = 'Mark as Delivered'
    
    def export_to_csv(self, request, queryset):
        """Export selected orders to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Customer', 'Phone', 'Email', 'Total Amount', 'Status', 'Payment Status', 'Date'])
        
        for order in queryset:
            writer.writerow([
                order.id,
                order.full_name,
                order.phone,
                order.user.email if order.user else 'N/A',
                order.total_amount,
                order.status,
                order.payment_status,
                order.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        self.message_user(request, f'{queryset.count()} order(s) exported successfully.')
        return response
    export_to_csv.short_description = 'Export to CSV'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'subtotal']
    list_filter = ['order__created_at']
    search_fields = ['order__id', 'product__name']
    readonly_fields = ['order', 'product', 'quantity', 'subtotal']
