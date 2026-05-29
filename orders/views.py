from django.contrib import messages
from django.db.models import Q
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
    total = sum(item.unit_price * item.quantity for item in order.items.all())
    return render(request, 'orders/confirmation.html', {'order': order, 'total': total})


def track_order(request):
    """Public order lookup by ID + phone."""
    order = None
    error = ''
    items_with_totals = []
    total = 0
    if request.method == 'POST':
        order_id = request.POST.get('order_id', '').strip()
        phone = request.POST.get('phone', '').strip()
        if order_id and phone:
            try:
                order = Order.objects.get(
                    Q(id=int(order_id)) & Q(client_phone__contains=phone)
                )
                for item in order.items.all():
                    subtotal = item.unit_price * item.quantity
                    items_with_totals.append({
                        'item': item,
                        'subtotal': subtotal,
                    })
                    total += subtotal
            except (Order.DoesNotExist, ValueError):
                error = 'No encontramos un pedido con esos datos. Verificá el numero y el telefono.'
        else:
            error = 'Completá numero de pedido y telefono.'

    return render(request, 'orders/track.html', {
        'order': order,
        'error': error,
        'items_with_totals': items_with_totals,
        'total': total,
    })
