from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Order
from .whatsapp import send_whatsapp


@receiver(post_save, sender=Order)
def notify_new_order(sender, instance, created, **kwargs):
    if not created:
        return

    items_text = ""
    total = 0
    for item in instance.items.all():
        subtotal = item.unit_price * item.quantity
        total += subtotal
        items_text += f"\n- {item.product.name} x{item.quantity} = ${subtotal}"

    message = f"""🛒 *Nuevo pedido #{instance.pk}*

👤 *Cliente:* {instance.client_name}
📱 *Tel:* {instance.client_phone}
📧 *Email:* {instance.client_email}
📝 *Notas:* {instance.notes}

📦 *Items:*{items_text}

💰 *Total:* ${total}

🔗 {settings.SITE_URL}/admin/orders/order/{instance.pk}/change/"""

    send_whatsapp(settings.WHATSAPP_NUMBER, message)
