from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category
from .forms import ReviewForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from orders.models import Order
from decimal import Decimal


def home(request):
    # Smart Trending: Best Sellers -> High Rated -> Newest
    products = Product.objects.filter(is_available=True).annotate(
        total_sales=Sum('orderitem__quantity')
    ).order_by('-total_sales', '-created_at')[:8]
    categories = Category.objects.all()
    context = {
        "products": products,
        "categories": categories
    }
    return render(request, "store/home.html", context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    # Get related products from same category
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(id=product.id).order_by('?')[:4]
    
    # Get reviews
    reviews = product.reviews.all()
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    # Handle review submission
    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            try:
                review.save()
                messages.success(request, 'Thank you for your review!')
                return redirect('product_detail', slug=slug)
            except:
                messages.error(request, 'You have already reviewed this product.')
    else:
        form = ReviewForm()
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'user_review': user_review,
        'review_form': form,
        'average_rating': product.get_average_rating(),
        'review_count': product.get_review_count(),
    }
    return render(request, "store/product_detail.html", context)


def products_list(request):
    """Product listing page with filters and search"""
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Category filter
    category_slug = request.GET.get('category', '')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)
    
    # Price filter (Premium Ranges)
    price_range = request.GET.get('price', '')
    if price_range == 'under-5000':
        products = products.filter(price__lt=5000)
    elif price_range == '5000-10000':
        products = products.filter(price__gte=5000, price__lt=10000)
    elif price_range == 'above-10000':
        products = products.filter(price__gte=10000)
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price-low':
        products = products.order_by('price')
    elif sort_by == 'price-high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:  # newest
        products = products.order_by('-created_at')
    
    # Stock filter
    in_stock = request.GET.get('in_stock', '')
    if in_stock == 'yes':
        products = products.filter(stock__gt=0)
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'price_range': price_range,
        'sort_by': sort_by,
        'in_stock': in_stock,
        'total_products': products.count()
    }
    
    return render(request, 'store/products_list.html', context)


@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with sales analytics and key metrics"""
    
    # Date filters
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Revenue calculations
    total_revenue = Order.objects.filter(
        payment_status__in=['completed', 'cod_pending']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    month_revenue = Order.objects.filter(
        created_at__gte=month_start,
        payment_status__in=['completed', 'cod_pending']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    today_revenue = Order.objects.filter(
        created_at__date=today,
        payment_status__in=['completed', 'cod_pending']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # Order counts
    total_orders = Order.objects.count()
    month_orders = Order.objects.filter(created_at__gte=month_start).count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Product stats
    total_products = Product.objects.count()
    available_products = Product.objects.filter(is_available=True).count()
    total_categories = Product.objects.values('category').distinct().count()
    
    # Low stock alerts
    low_stock_products = Product.objects.filter(
        stock__lte=5,
        stock__gt=0
    ).select_related('category').order_by('stock')[:10]
    
    out_of_stock_products = Product.objects.filter(stock=0).count()
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')[:10]
    
    # Status breakdown
    status_breakdown = Order.objects.values('status').annotate(count=Count('id'))
    
    context = {
        # Revenue
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'today_revenue': today_revenue,
        
        # Orders
        'total_orders': total_orders,
        'month_orders': month_orders,
        'today_orders': today_orders,
        'pending_orders': pending_orders,
        
        # Products
        'total_products': total_products,
        'available_products': available_products,
        'total_categories': total_categories,
        'out_of_stock_count': out_of_stock_products,
        
        # Alerts & Lists
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
        'status_breakdown': status_breakdown,
    }
    
    return render(request, 'admin/dashboard.html', context)
