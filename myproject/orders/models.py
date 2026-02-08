from django.db import models
from django.contrib.auth.models import User
from store.models import Product
from django.utils import timezone


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
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, blank=True, null=True)
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
    display_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Renaming total_amount to avoid confusion or just keeping it
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # ✅ FIELDS FOR ADMIN
    paid = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Timeline Fields (Professional Feature)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Payment Completed At")
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name="Shipped At")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Delivered At")
    
    # Audit Field
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_orders',
        verbose_name="Last Updated By"
    )

    def update_total(self):
        total = 0
        for item in self.items.all():
            total += item.subtotal
        self.total_amount = total
        self.save()
    
    def save(self, *args, **kwargs):
        """Auto-update timeline fields based on status changes"""
        if self.pk:  # Existing order
            old_order = Order.objects.get(pk=self.pk)
            
            # Track payment completion
            if old_order.payment_status != 'completed' and self.payment_status == 'completed':
                if not self.paid_at:
                    self.paid_at = timezone.now()
                self.paid = True # Sync paid boolean
            
            # Track shipping
            if old_order.status != 'shipped' and self.status == 'shipped':
                if not self.shipped_at:
                    self.shipped_at = timezone.now()
            
            # Track delivery
            if old_order.status != 'delivered' and self.status == 'delivered':
                if not self.delivered_at:
                    self.delivered_at = timezone.now()
        
        # Sync paid if payment_status is completed, for new orders too
        if self.payment_status == 'completed':
            self.paid = True

        super().save(*args, **kwargs)

    # ✅ METHOD USED BY ADMIN
    def total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def __str__(self):
        return f"Order #{self.id} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.price and self.product: # Ensure product exists
            self.price = self.product.price
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)

    # ✅ METHOD USED BY ADMIN
    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
