from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.products_list, name="products_list"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
]
