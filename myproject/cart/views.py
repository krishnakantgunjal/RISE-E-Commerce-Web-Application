from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from store.models import Product
from django.contrib import messages


def get_cart_total(cart):
    """Calculate total price of items in cart"""
    return sum(float(item['price']) * item['quantity'] for item in cart.values() if isinstance(item, dict))


def cart_detail(request):
    cart = request.session.get("cart", {})

    cart_items = []
    total = 0

    for product_id, item in cart.items():
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
            continue

    return render(request, "cart/cart_detail.html", {"cart_items": cart_items, "total": total})


def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    # Determine current quantity
    current_quantity = 0
    if product_id_str in cart and isinstance(cart[product_id_str], dict):
        current_quantity = cart[product_id_str]["quantity"]
    
    new_quantity = current_quantity + 1
    
    # Check Stock Availability
    if new_quantity > product.stock:
        msg = f"Sorry, only {product.stock} items available in stock."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': msg})
            
        messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'cart:cart_detail'))

    # Proceed to update logic
    if product_id_str in cart and isinstance(cart[product_id_str], dict):
        cart[product_id_str]["quantity"] = new_quantity
    else:
        cart[product_id_str] = {
            "quantity": 1,
            "price": str(product.price),
        }
    
    request.session["cart"] = cart
    request.session.modified = True

    # Return JSON for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'quantity': new_quantity,
            'subtotal': float(product.price) * new_quantity,
            'total_amount': get_cart_total(cart),
            'message': f"Updated {product.name} quantity to {new_quantity}."
        })

    # Standard Redirect
    if current_quantity == 0:
        messages.success(request, f"{product.name} added to cart.")
    else:
        messages.success(request, f"Updated {product.name} quantity to {new_quantity}.")

    return redirect("cart:cart_detail")


def cart_decrement(request, product_id):
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)
    
    new_quantity = 0
    removed = False

    if product_id_str in cart:
        if cart[product_id_str]["quantity"] > 1:
            cart[product_id_str]["quantity"] -= 1
            new_quantity = cart[product_id_str]["quantity"]
        else:
            del cart[product_id_str]
            removed = True
            
    request.session["cart"] = cart
    request.session.modified = True
    
    # Return JSON for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        total = get_cart_total(cart)
        product = get_object_or_404(Product, id=product_id) # Need fetching for price calc if not removed
        subtotal = float(product.price) * new_quantity if not removed else 0
        
        return JsonResponse({
            'status': 'success',
            'quantity': new_quantity,
            'subtotal': subtotal,
            'total_amount': total,
            'removed': removed,
            'message': "Item removed" if removed else "Quantity updated"
        })
    
    # Standard Redirect
    if removed:
        messages.success(request, "Item removed from cart.")
    else:
        messages.success(request, "Updated quantity.")
    
    return redirect(request.META.get('HTTP_REFERER', 'cart:cart_detail'))


def cart_remove(request, product_id):
    cart = request.session.get("cart", {})

    product_id_str = str(product_id)

    if product_id_str in cart:
        try:
            p = Product.objects.get(id=product_id)
            product_name = p.name
        except:
            product_name = "Item"
            
        del cart[product_id_str]
        messages.success(request, f"{product_name} removed from cart.")

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart:cart_detail")
