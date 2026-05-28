from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_type', 'discount_value', 'start_date', 'end_date', 'is_currently_active', 'is_active']
    list_filter = ['discount_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['products']
    date_hierarchy = 'start_date'
