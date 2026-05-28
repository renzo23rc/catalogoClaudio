from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def active_offer(product):
    """Return the first currently active offer for a product, or None."""
    now = timezone.now()
    return product.offers.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).first()


@register.filter
def discounted_price(product):
    """Return the discounted price for a product if an active offer exists."""
    now = timezone.now()
    offer = product.offers.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).first()
    if offer:
        return offer.get_discounted_price(product)
    return None
