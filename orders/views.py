from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product
from .cart import Cart
from .models import Order, OrderItem


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = Cart(request)
    qty = int(request.POST.get('quantity', 1))
    cart.add(product.id, qty)
    messages.success(request, f'"{product.name}" agregado al carrito.')
    return redirect(request.POST.get('next', request.META.get('HTTP_REFERER', 'orders:cart')))


def update_cart(request, product_id):
    cart = Cart(request)
    qty = int(request.POST.get('quantity', 1))
    cart.update(product_id, qty)
    return redirect('orders:cart')


def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    return redirect('orders:cart')


def cart_detail(request):
    cart = Cart(request)
    items = cart.get_items()
    total = cart.get_total()
    return render(request, 'orders/cart.html', {
        'items': items,
        'total': total,
        'cart_count': len(cart),
    })


def checkout(request):
    cart = Cart(request)
    items = cart.get_items()
    if not items:
        messages.info(request, 'Tu carrito esta vacio.')
        return redirect('orders:cart')

    if request.method == 'POST':
        name = request.POST.get('client_name', '').strip()
        phone = request.POST.get('client_phone', '').strip()
        email = request.POST.get('client_email', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not name or not phone or not email:
            messages.error(request, 'Completa todos los campos obligatorios.')
            return render(request, 'orders/checkout.html', {
                'items': items,
                'total': cart.get_total(),
                'cart_count': len(cart),
                'client_name': name,
                'client_phone': phone,
                'client_email': email,
                'notes': notes,
            })

        order = Order.objects.create(
            client_name=name,
            client_phone=phone,
            client_email=email,
            notes=notes,
        )
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['product'].base_price,
            )
        cart.clear()
        return redirect('orders:order_confirmation', order_id=order.id)

    return render(request, 'orders/checkout.html', {
        'items': items,
        'total': cart.get_total(),
        'cart_count': len(cart),
    })


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/confirmation.html', {'order': order})
