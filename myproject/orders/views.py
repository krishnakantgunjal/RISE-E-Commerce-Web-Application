from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from store.models import Product
from accounts.models import UserProfile
from .models import Order, OrderItem


def checkout(request):
    cart = request.session.get("cart", {})
    
    # Redirect if cart is empty
    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect("cart:cart_detail")

    cart_items = []
    total = 0

    for product_id, item in cart.items():
        # Skip if item is not a dictionary (malformed data)
        if not isinstance(item, dict):
            continue
            
        try:
            product = get_object_or_404(Product, id=product_id)

            quantity = item.get("quantity", 1)
            price = float(item.get("price", 0))
            subtotal = price * quantity

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "price": price,
                "subtotal": subtotal,
            })

            total += subtotal
        except (ValueError, Product.DoesNotExist):
            # Skip invalid items
            continue

    if request.method == "POST":
        # Final Stock Check
        for item in cart_items:
            product = item['product']
            quantity = item['quantity']
            if product.stock < quantity:
                messages.error(request, f"⚠️ Stock Error: {product.name} only has {product.stock} items left. Please update your cart.")
                return redirect("cart:cart_detail")

        full_name = request.POST.get("full_name")
        email = request.POST.get("email") # Capture email
        phone = request.POST.get("phone")
        
        # Capture detailed address fields
        pincode = request.POST.get("pincode")
        address_line1 = request.POST.get("address_line1")
        address_line2 = request.POST.get("address_line2")
        landmark = request.POST.get("landmark")
        city = request.POST.get("city")
        state = request.POST.get("state")
        
        # Construct full address string for backward compatibility
        full_address_parts = [
            f"{address_line1}, {address_line2}",
            f"Landmark: {landmark}" if landmark else "",
            f"{city}, {state} - {pincode}"
        ]
        formatted_address = "\n".join(filter(None, full_address_parts))

        # Save Default Address if requested
        if request.user.is_authenticated and request.POST.get('default_address'):
            UserProfile.objects.update_or_create(
                user=request.user,
                defaults={
                    'phone': phone,
                    'pincode': pincode,
                    'address_line1': address_line1,
                    'address_line2': address_line2,
                    'landmark': landmark,
                    'city': city,
                    'state': state
                }
            )

        # Create order with pending status
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            
            # Save breakdown
            pincode=pincode,
            address_line1=address_line1,
            address_line2=address_line2,
            landmark=landmark,
            city=city,
            state=state,
            
            # Save combined string
            address=formatted_address,
            
            total_amount=total,
            status='pending',
            payment_status='pending'
        )

        # Create order items (but don't reduce stock yet - wait for payment)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                price=item["price"],
                subtotal=item["subtotal"],
            )

        # Store order ID in session for payment page
        request.session['pending_order_id'] = order.id

        # Redirect to payment page instead of clearing cart
        return redirect("orders:payment_page", order_id=order.id)

    # Get User Profile for Pre-filling
    user_profile = None
    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
        except UserProfile.DoesNotExist:
            pass

    return render(request, "orders/checkout.html", {
        "cart_items": cart_items,
        "total": total,
        "user_profile": user_profile
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "orders/order_success.html", {"order": order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    return render(request, "orders/my_orders.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    """Detailed view of a specific order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def cancel_order(request, order_id):
    """Cancel an order if it's still pending"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status == 'pending':
        # Restore stock for cancelled order
        for item in order.items.all():
            item.product.increase_stock(item.quantity)
        
        order.status = 'cancelled'
        order.save()
        messages.success(request, f"Order #{order.id} has been cancelled successfully.")
    else:
        messages.error(request, f"Order #{order.id} cannot be cancelled (Status: {order.get_status_display()}).")
    
    return redirect('orders:order_detail', order_id=order_id)


def payment_page(request, order_id):
    """Display payment page with QR code (Demo Payment System)"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if order is already paid
    if order.payment_status == 'completed':
        return redirect('orders:order_success', order_id=order.id)
    
    context = {
        'order': order,
    }
    return render(request, 'orders/payment_page.html', context)


def process_payment(request, order_id):
    """Process demo payment and complete order"""
    # Only allow POST requests
    if request.method != 'POST':
        return redirect('orders:payment_page', order_id=order_id)
    
    order = get_object_or_404(Order, id=order_id)
    
    # Prevent duplicate payment processing
    if order.payment_status == 'completed':
        messages.info(request, 'This order has already been paid.')
        return redirect('orders:order_success', order_id=order.id)
    
    try:
        # Update order status
        order.payment_status = 'completed'
        order.status = 'processing'
        order.save()
        
        # Now reduce stock after payment confirmation
        for item in order.items.all():
            item.product.reduce_stock(item.quantity)
        
        # Safely clear cart
        request.session.pop('cart', None)
        request.session.modified = True
        
        messages.success(request, 'Payment completed successfully!')
        return redirect('orders:order_success', order_id=order.id)
        
    except ValueError as e:
        # Stock reduction failed
        messages.error(request, f'Payment processing error: {str(e)}')
        return redirect('orders:payment_page', order_id=order.id)
    except Exception as e:
        # Any other error
        messages.error(request, 'An error occurred while processing your payment. Please try again.')
        return redirect('orders:payment_page', order_id=order.id)


def thanks_visiting(request, order_id):
    """Render the thank you/project demonstration page"""
    return render(request, "orders/thanks_visiting.html", {'order_id': order_id})
