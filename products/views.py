from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from offers.models import Offer
from .models import Category, Product


class AboutView(TemplateView):
    template_name = 'products/about.html'


class ContactView(TemplateView):
    template_name = 'products/contact.html'


class HowToBuyView(TemplateView):
    template_name = 'products/how_to_buy.html'


class HomeView(TemplateView):
    template_name = 'products/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent=None, is_active=True)

        featured = list(Product.objects.filter(is_active=True).prefetch_related('images', 'offers')[:6])
        context['featured_products'] = featured

        now = timezone.now()
        active_offers = Offer.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).prefetch_related('products')

        offer_products = []
        seen = set()
        for offer in active_offers:
            for product in offer.products.filter(is_active=True):
                if product.id not in seen:
                    seen.add(product.id)
                    offer_products.append({
                        'product': product,
                        'discounted_price': offer.get_discounted_price(product),
                        'offer': offer,
                    })
        context['offer_products'] = offer_products
        return context


class CategoryListView(ListView):
    model = Product
    template_name = 'products/category_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        category_ids = {self.category.id}
        for descendant in self.category.get_descendants():
            category_ids.add(descendant.id)
        qs = Product.objects.filter(
            category_id__in=category_ids,
            is_active=True
        ).prefetch_related('images', 'offers')
        if self.request.GET.get('on_offer') == 'true':
            now = timezone.now()
            qs = qs.filter(
                offers__is_active=True,
                offers__start_date__lte=now,
                offers__end_date__gte=now
            ).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['on_offer'] = self.request.GET.get('on_offer') == 'true'
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context['images'] = product.images.all().order_by('-is_primary', 'order')
        context['primary_image'] = product.images.filter(is_primary=True).first()
        context['other_images'] = product.images.filter(is_primary=False).order_by('order')

        now = timezone.now()
        active_offer = product.offers.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).first()
        if active_offer:
            context['active_offer'] = active_offer
            context['discounted_price'] = active_offer.get_discounted_price(product)
        return context


class SearchView(ListView):
    model = Product
    template_name = 'products/search.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        qs = Product.objects.filter(is_active=True).prefetch_related('images', 'offers')
        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context
