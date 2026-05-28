from django.conf import settings


def cart_count(request):
    cart = request.session.get('cart', {})
    return {'cart_count': sum(cart.values())}


def whatsapp_settings(request):
    return {
        'WHATSAPP_NUMBER': settings.WHATSAPP_NUMBER,
    }
