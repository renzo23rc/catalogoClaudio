from django.urls import path

from .views import (
    AboutView,
    CategoryListView,
    ContactView,
    HomeView,
    HowToBuyView,
    ProductDetailView,
    SearchView,
)

app_name = 'products'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('quienes-somos/', AboutView.as_view(), name='about'),
    path('contacto/', ContactView.as_view(), name='contact'),
    path('como-comprar/', HowToBuyView.as_view(), name='how_to_buy'),
    path('categoria/<slug:slug>/', CategoryListView.as_view(), name='category'),
    path('producto/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('buscar/', SearchView.as_view(), name='search'),
]
