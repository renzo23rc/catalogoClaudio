from django.db import models
from django.utils import timezone


class Offer(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Porcentaje'),
        ('fixed', 'Monto fijo'),
    ]
    name = models.CharField(max_length=255, verbose_name='nombre')
    description = models.TextField(blank=True, verbose_name='descripcion')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, verbose_name='tipo de descuento')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='valor')
    start_date = models.DateTimeField(verbose_name='fecha inicio')
    end_date = models.DateTimeField(verbose_name='fecha fin')
    is_active = models.BooleanField(default=True, verbose_name='activa')
    products = models.ManyToManyField('products.Product', related_name='offers', verbose_name='productos')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'oferta'
        verbose_name_plural = 'ofertas'

    def __str__(self):
        return self.name

    @property
    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def get_discounted_price(self, product):
        if self.discount_type == 'percentage':
            return product.base_price * (1 - self.discount_value / 100)
        elif self.discount_type == 'fixed':
            return max(0, product.base_price - self.discount_value)
        return product.base_price
