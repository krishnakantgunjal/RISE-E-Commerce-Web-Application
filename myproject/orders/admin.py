from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.contrib import messages
import csv
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'price', 'subtotal')
    can_delete = False
    
    def get_readonly_fields(self, request, obj=None):
        """Lock order items after payment is completed"""
        if obj and obj.payment_status == 'completed':
            return ('product', 'quantity', 'price', 'subtotal')
        return ('price', 'subtotal')
    
    def has_add_permission(self, request, obj=None):
        """Prevent adding items after payment is completed"""
        if obj and obj.payment_status == 'completed':
            return False
        return super().has_add_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting items after payment is completed"""
        if obj and obj.payment_status == 'completed':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_id_display', 
        'customer_name', 
        'phone', 
        'total_amount_display',
        'status_badge', 
        'payment_badge', 
        'created_at_display'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['id', 'full_name', 'phone', 'email', 'user__username', 'user__email']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'full_name', 'email', 'phone'),
            'description': 'Customer details and contact information'
        }),
        ('Shipping Address', {
            'fields': ('address_line1', 'address_line2', 'landmark', 'city', 'state', 'pincode'),
            'classes': ('collapse',),
        }),
        ('Order Summary', {
            'fields': ('total_amount', 'created_at'),
            'description': 'Order financial details'
        }),
        ('Order Status', {
            'fields': ('status', 'payment_status'),
            'description': 'Current order and payment status'
        }),
        ('Order Timeline', {
            'fields': ('paid_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',),
            'description': 'Automatic timestamps for order progression'
        }),
        ('Audit Information', {
            'fields': ('updated_by',),
            'classes': ('collapse',),
            'description': 'Track who last modified this order'
        }),
    )
    
    actions = [
        'mark_processing', 
        'mark_shipped', 
        'mark_delivered', 
        'mark_cancelled',
        'export_to_csv'
    ]
    
    def get_readonly_fields(self, request, obj=None):
        """
        Conditional readonly fields based on payment status.
        Once payment is completed, lock sensitive fields.
        """
        # Timeline and audit fields are always readonly (auto-populated)
        base_readonly = [
            'created_at', 
            'total_amount', 
            'paid_at', 
            'shipped_at', 
            'delivered_at',
            'updated_by'
        ]
        
        if obj and obj.payment_status == 'completed':
            # Lock everything except order status after payment
            return base_readonly + [
                'user', 
                'full_name', 
                'email', 
                'phone',
                'address_line1',
                'address_line2',
                'landmark',
                'city',
                'state',
                'pincode',
                'payment_status'
            ]
        
        return base_readonly
    
    # ===== CUSTOM DISPLAY METHODS =====
    
    def order_id_display(self, obj):
        """Display order ID with formatting"""
        return format_html(
            '<strong style="color: #6366f1;">#{}</strong>',
            obj.id
        )
    order_id_display.short_description = 'Order ID'
    order_id_display.admin_order_field = 'id'
    
    def customer_name(self, obj):
        """Display customer name with user link if available"""
        if obj.user:
            return format_html(
                '{} <span style="color: #64748b;">({})</span>',
                obj.full_name,
                obj.user.username
            )
        return obj.full_name
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'full_name'
    
    def total_amount_display(self, obj):
        """Display total amount with currency"""
        return format_html(
            '<strong style="color: #10b981;">₹{:,.2f}</strong>',
            obj.total_amount
        )
    total_amount_display.short_description = 'Total'
    total_amount_display.admin_order_field = 'total_amount'
    
    def created_at_display(self, obj):
        """Display formatted creation date"""
        return obj.created_at.strftime('%d %b %Y, %I:%M %p')
    created_at_display.short_description = 'Order Date'
    created_at_display.admin_order_field = 'created_at'
    
    def status_badge(self, obj):
        """Display status with professional color coding"""
        colors = {
            'pending': '#fbbf24',      # Amber
            'processing': '#3b82f6',   # Blue
            'shipped': '#8b5cf6',      # Purple
            'delivered': '#10b981',    # Green
            'cancelled': '#ef4444'     # Red
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 14px; '
            'border-radius: 14px; font-weight: 700; font-size: 11px; '
            'text-transform: uppercase; letter-spacing: 0.5px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Order Status'
    status_badge.admin_order_field = 'status'
    
    def payment_badge(self, obj):
        """Display payment status with color coding"""
        colors = {
            'pending': '#fbbf24',    # Amber
            'completed': '#10b981',  # Green
            'failed': '#ef4444',     # Red
        }
        icons = {
            'pending': '⏳',
            'completed': '✓',
            'failed': '✗',
        }
        color = colors.get(obj.payment_status, '#6c757d')
        icon = icons.get(obj.payment_status, '•')
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 14px; '
            'border-radius: 14px; font-weight: 700; font-size: 11px; '
            'text-transform: uppercase; letter-spacing: 0.5px;">{} {}</span>',
            color, icon, obj.get_payment_status_display()
        )
    payment_badge.short_description = 'Payment'
    payment_badge.admin_order_field = 'payment_status'
    
    # ===== CUSTOM ACTIONS WITH BUSINESS LOGIC =====
    
    def mark_processing(self, request, queryset):
        """Mark orders as processing (only if payment is completed)"""
        valid_orders = queryset.filter(payment_status='completed', status='pending')
        invalid_count = queryset.exclude(payment_status='completed').count()
        
        updated = valid_orders.update(status='processing')
        
        if updated:
            self.message_user(
                request, 
                f'{updated} order(s) marked as Processing.',
                messages.SUCCESS
            )
        
        if invalid_count:
            self.message_user(
                request,
                f'{invalid_count} order(s) skipped (payment not completed).',
                messages.WARNING
            )
    mark_processing.short_description = '✓ Mark as Processing (Payment Required)'
    
    def mark_shipped(self, request, queryset):
        """Mark orders as shipped (only if processing)"""
        valid_orders = queryset.filter(status='processing', payment_status='completed')
        invalid_count = queryset.exclude(status='processing').count()
        
        updated = valid_orders.update(status='shipped')
        
        if updated:
            self.message_user(
                request,
                f'{updated} order(s) marked as Shipped.',
                messages.SUCCESS
            )
        
        if invalid_count:
            self.message_user(
                request,
                f'{invalid_count} order(s) skipped (must be in Processing status).',
                messages.WARNING
            )
    mark_shipped.short_description = '📦 Mark as Shipped (Processing Required)'
    
    def mark_delivered(self, request, queryset):
        """Mark orders as delivered (only if shipped)"""
        valid_orders = queryset.filter(status='shipped', payment_status='completed')
        invalid_count = queryset.exclude(status='shipped').count()
        
        updated = valid_orders.update(status='delivered')
        
        if updated:
            self.message_user(
                request,
                f'{updated} order(s) marked as Delivered.',
                messages.SUCCESS
            )
        
        if invalid_count:
            self.message_user(
                request,
                f'{invalid_count} order(s) skipped (must be in Shipped status).',
                messages.WARNING
            )
    mark_delivered.short_description = '✓ Mark as Delivered (Shipped Required)'
    
    def mark_cancelled(self, request, queryset):
        """Cancel orders (only if not delivered)"""
        valid_orders = queryset.exclude(status='delivered')
        invalid_count = queryset.filter(status='delivered').count()
        
        updated = valid_orders.update(status='cancelled')
        
        if updated:
            self.message_user(
                request,
                f'{updated} order(s) cancelled.',
                messages.SUCCESS
            )
        
        if invalid_count:
            self.message_user(
                request,
                f'{invalid_count} order(s) cannot be cancelled (already delivered).',
                messages.ERROR
            )
    mark_cancelled.short_description = '✗ Cancel Orders (Not Delivered)'
    
    def export_to_csv(self, request, queryset):
        """Export selected orders to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Order ID', 'Customer', 'Phone', 'Email', 
            'Total Amount', 'Order Status', 'Payment Status', 
            'Order Date'
        ])
        
        for order in queryset:
            writer.writerow([
                f'#{order.id}',
                order.full_name,
                order.phone,
                order.email or (order.user.email if order.user else 'N/A'),
                f'₹{order.total_amount}',
                order.get_status_display(),
                order.get_payment_status_display(),
                order.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        self.message_user(
            request, 
            f'{queryset.count()} order(s) exported successfully.',
            messages.SUCCESS
        )
        return response
    export_to_csv.short_description = '📊 Export to CSV'
    
    def save_model(self, request, obj, form, change):
        """
        Enforce business rules before saving.
        Prevent invalid status transitions.
        Track who made the changes (audit).
        """
        if change:  # Editing existing order
            old_obj = Order.objects.get(pk=obj.pk)
            
            # Rule: Cannot ship if payment is pending
            if obj.status == 'shipped' and obj.payment_status != 'completed':
                messages.error(
                    request,
                    'Cannot mark as Shipped: Payment is not completed.'
                )
                return
            
            # Rule: Cannot revert from delivered
            if old_obj.status == 'delivered' and obj.status != 'delivered':
                messages.error(
                    request,
                    'Cannot change status: Order is already delivered.'
                )
                return
        
        # Audit: Track who updated the order
        if change and request.user.is_authenticated:
            obj.updated_by = request.user
        
        super().save_model(request, obj, form, change)


# OrderItem is intentionally NOT registered as a standalone admin model.
# It should only be managed through OrderItemInline within OrderAdmin.
# This prevents:
#   - Accidental data corruption
#   - Invalid order item creation outside order context
#   - 500 errors from permission conflicts
# 
# To view order items, navigate to the specific Order in admin.


# Customize admin site headers
admin.site.site_header = "RISE E-Commerce Admin"
admin.site.site_title = "RISE Admin Portal"
admin.site.index_title = "Order Management System"
