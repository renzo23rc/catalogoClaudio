import csv
import io
from decimal import Decimal

from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .models import Category, Product, ProductImage


class LowStockFilter(admin.SimpleListFilter):
    title = _('bajo stock')
    parameter_name = 'low_stock'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Si (por debajo del umbral)')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            from django.db.models import F
            return queryset.filter(stock_quantity__lt=F('min_stock_threshold'))
        return queryset


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_primary', 'alt_text', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'category', 'is_featured', 'stock_quantity',
        'stock_quantity_colored', 'min_stock_threshold', 'base_price', 'is_active'
    ]
    list_filter = ['category', 'is_active', 'is_featured', LowStockFilter]
    search_fields = ['name', 'sku', 'description']
    list_editable = ['stock_quantity', 'min_stock_threshold', 'is_featured']
    inlines = [ProductImageInline]
    actions = ['export_to_csv', 'mark_inactive', 'set_stock_to_zero']
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description=_('stock'))
    def stock_quantity_colored(self, obj):
        if obj.stock_quantity == 0:
            color = 'red'
        elif obj.stock_quantity < obj.min_stock_threshold:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.stock_quantity
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'importar-csv/',
                self.admin_site.admin_view(self.import_csv),
                name='products_product_import_csv',
            ),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        from .forms import CSVImportForm
        if request.method == 'POST':
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                reader = csv.DictReader(
                    io.StringIO(csv_file.read().decode('utf-8'))
                )
                created = 0
                errors = []
                for row in reader:
                    try:
                        from .models import Category
                        category = Category.objects.get(
                            slug=row.get('category_slug', '')
                        )
                        Product.objects.create(
                            name=row['name'],
                            slug=row.get('slug', slugify(row['name'])),
                            sku=row['sku'],
                            description=row.get('description', ''),
                            base_price=Decimal(row['base_price']),
                            category=category,
                            stock_quantity=int(row.get('stock_quantity', 0)),
                        )
                        created += 1
                    except Exception as e:
                        errors.append(f'Fila {reader.line_num}: {e}')
                messages.success(
                    request, f'{created} producto(s) importados.'
                )
                for err in errors:
                    messages.warning(request, err)
                return redirect('..')
        else:
            form = CSVImportForm()
        return render(
            request,
            'admin/products/product/import_csv.html',
            {'form': form},
        )

    @admin.action(description=_('Exportar seleccionados a CSV'))
    def export_to_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename=productos.csv'
        )
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)
        return response

    @admin.action(description=_('Marcar como inactivo'))
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f'{updated} producto(s) marcado(s) como inactivo(s).'
        )

    @admin.action(description=_('Establecer stock en cero'))
    def set_stock_to_zero(self, request, queryset):
        updated = queryset.update(stock_quantity=0)
        self.message_user(
            request, f'{updated} producto(s) con stock establecido en 0.'
        )


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
