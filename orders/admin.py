from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'quantity', 'unit_price']
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'client_name', 'status_colored', 'items_count', 'total_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['client_name', 'client_phone', 'client_email']
    readonly_fields = ['client_name', 'client_phone', 'client_email', 'notes', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']
    date_hierarchy = 'created_at'

    fieldsets = [
        ('Cliente', {'fields': ['client_name', 'client_phone', 'client_email']}),
        ('Pedido', {'fields': ['notes', 'status']}),
        ('Fechas', {'fields': ['created_at', 'updated_at']}),
    ]

    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'completed': 'green',
            'cancelled': 'red',
        }
        labels = {
            'pending': 'Pendiente',
            'confirmed': 'Confirmado',
            'completed': 'Completado',
            'cancelled': 'Cancelado',
        }
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            colors.get(obj.status, 'gray'),
            labels.get(obj.status, obj.status)
        )
    status_colored.short_description = 'estado'

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'items'

    def total_display(self, obj):
        total = sum(item.unit_price * item.quantity for item in obj.items.all())
        return f'${total}'
    total_display.short_description = 'total'

    @admin.action(description='Marcar como confirmado')
    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')

    @admin.action(description='Marcar como completado')
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')

    @admin.action(description='Marcar como cancelado')
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
