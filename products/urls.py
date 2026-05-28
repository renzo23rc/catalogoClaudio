from django.urls import path

from .views import CategoryListView, HomeView, ProductDetailView, SearchView

app_name = 'products'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('categoria/<slug:slug>/', CategoryListView.as_view(), name='category'),
    path('producto/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('buscar/', SearchView.as_view(), name='search'),
]
