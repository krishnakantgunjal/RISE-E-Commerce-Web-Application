from django.db import models
from django.contrib.auth.models import User
from store.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, blank=True, null=True)  # Added email field
    phone = models.CharField(max_length=15)
    
    # Detailed Address Fields
    pincode = models.CharField(max_length=10, default="")
    address_line1 = models.CharField(max_length=255, verbose_name="Flat, House no., Building, Company, Apartment", default="")
    address_line2 = models.CharField(max_length=255, verbose_name="Area, Street, Sector, Village", default="")
    landmark = models.CharField(max_length=255, blank=True, null=True, default="")
    city = models.CharField(max_length=100, default="")
    state = models.CharField(max_length=100, default="")
    
    # We will keep the original address field for backward compatibility or full formatted address
    address = models.TextField(blank=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def update_total(self):
        total = 0
        for item in self.items.all():
            total += item.subtotal
        self.total_amount = total
        self.save()

    def __str__(self):
        return f"Order #{self.id} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
