import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from .models import Category, Product, ProductImage


class LowStockFilter(admin.SimpleListFilter):
    title = _('bajo stock')
    parameter_name = 'low_stock'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Si (menos de 10)')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(stock_quantity__lt=10)
        return queryset


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_primary', 'alt_text', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'stock_quantity', 'base_price', 'is_active']
    list_filter = ['category', 'is_active', LowStockFilter]
    search_fields = ['name', 'sku', 'description']
    list_editable = ['stock_quantity']
    inlines = [ProductImageInline]
    actions = ['export_to_csv', 'mark_inactive', 'set_stock_to_zero']
    prepopulated_fields = {'slug': ('name',)}

    @admin.action(description=_('Exportar seleccionados a CSV'))
    def export_to_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=productos.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)
        return response

    @admin.action(description=_('Marcar como inactivo'))
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} producto(s) marcado(s) como inactivo(s).')

    @admin.action(description=_('Establecer stock en cero'))
    def set_stock_to_zero(self, request, queryset):
        updated = queryset.update(stock_quantity=0)
        self.message_user(request, f'{updated} producto(s) con stock establecido en 0.')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'order']
    list_filter = ['is_primary']
    search_fields = ['product__name', 'alt_text']
