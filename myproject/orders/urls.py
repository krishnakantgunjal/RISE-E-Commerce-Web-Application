from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("success/<int:order_id>/", views.order_success, name="order_success"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
    path("order/<int:order_id>/cancel/", views.cancel_order, name="cancel_order"),
    path("payment/<int:order_id>/", views.payment_page, name="payment_page"),
    path("payment/<int:order_id>/process/", views.process_payment, name="process_payment"),
    path("thanks-visiting/<int:order_id>/", views.thanks_visiting, name="thanks_visiting"),
]
