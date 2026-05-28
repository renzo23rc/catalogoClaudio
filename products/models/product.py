from django.db import models
from django.utils.text import slugify

from .category import Category


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='nombre')
    slug = models.SlugField(unique=True, verbose_name='slug')
    sku = models.CharField(max_length=100, unique=True, verbose_name='SKU')
    description = models.TextField(blank=True, verbose_name='descripcion')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='precio base')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='categoria'
    )
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name='stock')
    min_stock_threshold = models.PositiveIntegerField(default=10, verbose_name='stock minimo')
    is_active = models.BooleanField(default=True, verbose_name='activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='actualizado')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'producto'
        verbose_name_plural = 'productos'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
