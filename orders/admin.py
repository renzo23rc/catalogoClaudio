from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'unit_price']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'client_name', 'status', 'created_at', 'items_count']
    list_filter = ['status', 'created_at']
    search_fields = ['client_name', 'client_email', 'client_phone']
    readonly_fields = ['client_name', 'client_phone', 'client_email', 'notes', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    fieldsets = (
        (None, {
            'fields': ('status',)
        }),
        ('Cliente', {
            'fields': ('client_name', 'client_phone', 'client_email')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'items'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
