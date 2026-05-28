from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Order


@receiver(post_save, sender=Order)
def notify_new_order(sender, instance, created, **kwargs):
    if not created:
        return

    subject = f'Nuevo pedido #{instance.pk} - {instance.client_name}'

    items = [
        {
            'product': item.product,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'subtotal': item.unit_price * item.quantity,
        }
        for item in instance.items.all()
    ]
    total = sum(item['subtotal'] for item in items)

    html_message = render_to_string('orders/email/new_order.html', {
        'order': instance,
        'items': items,
        'total': total,
        'site_url': settings.SITE_URL,
    })

    text_message = f"""
Nuevo pedido #{instance.pk}
Cliente: {instance.client_name}
Telefono: {instance.client_phone}
Email: {instance.client_email}
Notas: {instance.notes}

Items:
{chr(10).join(f'  - {item.product.name} x{item.quantity} = ${item.unit_price * item.quantity}' for item in instance.items.all())}

Total: ${total}

Admin: {settings.SITE_URL}/admin/orders/order/{instance.pk}/change/
"""

    send_mail(
        subject=subject,
        message=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.NOTIFICATION_EMAIL],
        html_message=html_message,
        fail_silently=True,
    )
