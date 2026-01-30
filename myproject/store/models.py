from django.db import models
from django.contrib.auth.models import User
from django.utils.html import format_html
from cloudinary.models import CloudinaryField


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_product_count(self):
        return self.products.count()
    get_product_count.short_description = 'Products'


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    # ✅ CLOUDINARY FIELD - uploads directly to cloud storage
    image = CloudinaryField('image', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_stock_status(self):
        if self.stock == 0:
            return format_html('<span style="color: red; font-weight: bold;">Out of Stock</span>')
        elif self.stock < 10:
            return format_html('<span style="color: orange; font-weight: bold;">Low Stock ({} left)</span>', self.stock)
        else:
            return format_html('<span style="color: green; font-weight: bold;">In Stock</span>')
    get_stock_status.short_description = 'Stock Status'

    def admin_thumbnail(self):
        if self.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 8px;" />', self.image.url)
        return format_html('<span style="color: gray;">No Image</span>')
    admin_thumbnail.short_description = 'Preview'

    @property
    def is_low_stock(self):
        """Check if product has low stock (less than 10 units)"""
        return 0 < self.stock < 10

    def get_average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews:
            total = sum(review.rating for review in reviews)
            return round(total / len(reviews), 1)
        return 0

    def get_review_count(self):
        """Get total number of reviews"""
        return self.reviews.count()

    def reduce_stock(self, quantity):
        """Reduce stock after successful payment"""
        if self.stock >= quantity:
            self.stock -= quantity
            if self.stock == 0:
                self.is_available = False
            self.save()
        else:
            raise ValueError(f"Insufficient stock for {self.name}")

    def increase_stock(self, quantity):
        """Increase stock (e.g., when order is cancelled)"""
        self.stock += quantity
        if self.stock > 0:
            self.is_available = True
        self.save()



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
        unique_together = ('product', 'user')

    def __str__(self):
        return f'{self.user.username} - {self.product.name} ({self.rating} stars)'
