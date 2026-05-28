from django.db import models


class Order(models.Model):
    STATUS = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    client_name = models.CharField(max_length=200, verbose_name='nombre')
    client_phone = models.CharField(max_length=50, verbose_name='telefono')
    client_email = models.EmailField(verbose_name='email')
    notes = models.TextField(blank=True, verbose_name='notas')
    status = models.CharField(max_length=20, choices=STATUS, default='pending', verbose_name='estado')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'

    def __str__(self):
        return f"Pedido #{self.pk} - {self.client_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, verbose_name='producto')
    quantity = models.PositiveIntegerField(verbose_name='cantidad')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='precio unitario')

    class Meta:
        verbose_name = 'item'
        verbose_name_plural = 'items'

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
