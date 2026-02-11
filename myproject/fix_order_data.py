import os
import django
import sys
from django.utils import timezone

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from orders.models import Order

def fix_payment_sync():
    print("Starting sync of payment_status -> paid...")
    orders = Order.objects.all()
    count = 0
    
    for order in orders:
        original_paid = order.paid
        
        # Apply the logic: paid = True if and only if payment_status == 'completed'
        if order.payment_status == 'completed':
            order.paid = True
            # Also ensure paid_at is set if completed
            if not order.paid_at:
                order.paid_at = timezone.now()
        else:
            order.paid = False
            
        # Only save if changed or if we want to trigger the model save logic just in case
        if original_paid != order.paid or (order.payment_status == 'completed' and not order.paid_at):
            order.save()
            count += 1
            print(f"Updated Order #{order.id}: payment_status='{order.payment_status}' -> paid={order.paid}")
    
    print(f"Sync complete. Updated {count} orders.")

if __name__ == "__main__":
    try:
        fix_payment_sync()
    except Exception as e:
        print(f"Error during sync: {e}")
