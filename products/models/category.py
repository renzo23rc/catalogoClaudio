from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='nombre')
    slug = models.SlugField(unique=True, verbose_name='slug')
    description = models.TextField(blank=True, verbose_name='descripcion')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='categoria padre'
    )
    is_active = models.BooleanField(default=True, verbose_name='activa')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='creado')

    class Meta:
        ordering = ['name']
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_descendants(self):
        """Return all descendant categories (recursive, N+1 acceptable for shallow trees)."""
        descendants = []
        children = Category.objects.filter(parent=self)
        for child in children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
