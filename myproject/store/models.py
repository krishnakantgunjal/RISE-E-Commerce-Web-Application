from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User

# Stock threshold for low stock warnings
LOW_STOCK_THRESHOLD = 5


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, verbose_name="Category URL")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def get_product_count(self):
        """Get total products in this category"""
        return self.products.count()
    get_product_count.short_description = 'Products'


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, verbose_name="Product URL")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def admin_thumbnail(self):
        """Display thumbnail in admin list view"""
        if self.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />', self.image.url)
        return mark_safe('<span style="color: #999;">No Image</span>')
    admin_thumbnail.short_description = 'Image'
    
    def get_stock_status(self):
        """Get stock status with color coding"""
        if self.stock == 0:
            return mark_safe('<span style="color: #dc3545; font-weight: bold;">Out of Stock</span>')
        elif self.stock <= LOW_STOCK_THRESHOLD:
            return format_html('<span style="color: #ffc107; font-weight: bold;">Low Stock ({})</span>', self.stock)
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">In Stock ({})</span>', self.stock)
    get_stock_status.short_description = 'Stock Status'
    
    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return 0 < self.stock <= LOW_STOCK_THRESHOLD
    
    def reduce_stock(self, quantity):
        """Reduce stock by quantity"""
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity):
        """Increase stock by quantity"""
        self.stock += quantity
        self.save()
    
    def get_average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews:
            return round(sum(r.rating for r in reviews) / len(reviews), 1)
        return 0
    
    def get_review_count(self):
        """Get total number of reviews"""
        return self.reviews.count()


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')  # One review per user per product
    
    def __str__(self):
        return f'{self.user.username} - {self.product.name} ({self.rating}★)'

