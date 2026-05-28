from django.contrib import admin
from django.contrib.auth.models import Group

admin.site.unregister(Group)

admin.site.site_header = 'Catalogo — Administracion'
admin.site.site_title = 'Catalogo Admin'
admin.site.index_title = 'Panel de control'
