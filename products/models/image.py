import os

from django.db import models

from .product import Product


def product_image_path(instance, filename):
    """Upload images to products/<sku>/<filename>."""
    return f"products/{instance.product.sku}/{filename}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='producto'
    )
    image = models.ImageField(upload_to=product_image_path, verbose_name='imagen')
    is_primary = models.BooleanField(default=False, verbose_name='principal')
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='texto alternativo')
    order = models.PositiveIntegerField(default=0, verbose_name='orden')

    class Meta:
        ordering = ['order']
        verbose_name = 'imagen de producto'
        verbose_name_plural = 'imagenes de productos'

    def __str__(self):
        return f"Imagen de {self.product.name}"
