from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('carrito/', views.cart_detail, name='cart'),
    path('carrito/agregar/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('carrito/actualizar/<int:product_id>/', views.update_cart, name='update_cart'),
    path('carrito/eliminar/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('pedido/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
]
