from django.contrib import admin
from .models import Category, Product, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'get_product_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['admin_thumbnail', 'name', 'category', 'price', 'stock', 'get_stock_status', 'is_available', 'created_at']
    list_filter = ['category', 'is_available', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock', 'is_available']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['admin_thumbnail', 'created_at']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock', 'is_available')
        }),
        ('Media', {
            'fields': ('image', 'admin_thumbnail')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['make_available', 'make_unavailable', 'mark_out_of_stock']
    
    def make_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} product(s) marked as available.')
    make_available.short_description = 'Mark selected as available'
    
    def make_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} product(s) marked as unavailable.')
    make_unavailable.short_description = 'Mark selected as unavailable'
    
    def mark_out_of_stock(self, request, queryset):
        updated = queryset.update(stock=0, is_available=False)
        self.message_user(request, f'{updated} product(s) marked as out of stock.')
    mark_out_of_stock.short_description = 'Mark as out of stock'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    readonly_fields = ['created_at']


# Customize admin site
admin.site.site_header = 'RISE E-Commerce Admin'
admin.site.site_title = 'RISE Admin Portal'
admin.site.index_title = 'Welcome to RISE Store Management'
