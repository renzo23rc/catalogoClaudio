from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

from .models import Offer
from orders.whatsapp import send_group


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_type', 'discount_value', 'start_date', 'end_date', 'is_currently_active', 'is_active']
    list_filter = ['discount_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['products']
    date_hierarchy = 'start_date'
    actions = ['broadcast_offer']

    @admin.action(description='Difundir oferta por WhatsApp al grupo')
    def broadcast_offer(self, request, queryset):
        if not settings.WHATSAPP_GROUP_ID:
            self.message_user(request, 'Configura WHATSAPP_GROUP_ID en el .env primero.', level='ERROR')
            return

        sent = 0
        for offer in queryset:
            discount = f"{offer.discount_value}%" if offer.discount_type == 'percentage' else f"${offer.discount_value}"
            products_sample = list(offer.products.filter(is_active=True).values_list('name', flat=True)[:5])
            products_text = "\n".join(f"• {p}" for p in products_sample)
            if offer.products.count() > 5:
                products_text += f"\n... y {offer.products.count() - 5} mas"

            start = offer.start_date.strftime('%d/%m/%Y') if offer.start_date else '—'
            end = offer.end_date.strftime('%d/%m/%Y') if offer.end_date else '—'

            message = f"""🔥 *OFERTA: {offer.name}*

💲 {discount} de descuento
📅 Del {start} al {end}

📦 *Productos incluidos:*
{products_text}

👉 {settings.SITE_URL}/?on_offer=true"""

            if send_group(settings.WHATSAPP_GROUP_ID, message):
                sent += 1

        if sent:
            self.message_user(request, f'{sent} oferta(s) difundidas por WhatsApp.')
        else:
            self.message_user(
                request,
                'No se pudo enviar automaticamente. Configura UltraMsg en el .env o usa el link manual.',
                level='WARNING'
            )
