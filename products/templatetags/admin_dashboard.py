from django import template
from django.db.models import Sum, F
from django.utils import timezone

from offers.models import Offer
from orders.models import Order
from products.models import Product, Category

register = template.Library()


@register.inclusion_tag('admin/dashboard_cards.html')
def admin_dashboard():
    now = timezone.now()

    pending = Order.objects.filter(status='pending').count()
    low_stock = sum(
        1 for p in Product.objects.filter(is_active=True)
        if p.stock_quantity < p.min_stock_threshold
    )
    active_offers = Offer.objects.filter(
        is_active=True, start_date__lte=now, end_date__gte=now
    ).count()
    total = Product.objects.filter(is_active=True).count()

    recent_orders = Order.objects.filter(
        status='pending'
    ).order_by('-created_at')[:5].prefetch_related('items__product')

    # Calculate totals for each order
    for order in recent_orders:
        order.total_amount = sum(
            item.unit_price * item.quantity for item in order.items.all()
        )

    return {
        'pending_orders': pending,
        'low_stock': low_stock,
        'active_offers': active_offers,
        'total_products': total,
        'recent_orders': recent_orders,
        'cards': [
            {'label': 'Pedidos pendientes', 'count': pending, 'color': '#ea580c', 'url': '/admin/orders/order/?status__exact=pending'},
            {'label': 'Stock bajo', 'count': low_stock, 'color': '#dc2626', 'url': '/admin/products/product/'},
            {'label': 'Ofertas activas', 'count': active_offers, 'color': '#059669', 'url': '/admin/offers/offer/'},
            {'label': 'Productos activos', 'count': total, 'color': '#2563eb', 'url': '/admin/products/product/'},
        ],
    }
