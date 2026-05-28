import pytest
from django.urls import reverse
from products.models import Category, Product

@pytest.mark.django_db
class TestHomeView:
    def test_home_status(self, client):
        response = client.get(reverse('products:home'))
        assert response.status_code == 200

    def test_home_shows_categories(self, client):
        cat = Category.objects.create(name="Bebidas", slug="bebidas")
        response = client.get(reverse('products:home'))
        assert "Bebidas" in response.content.decode()

@pytest.mark.django_db
class TestCategoryListView:
    def test_category_page(self, client):
        cat = Category.objects.create(name="Bebidas", slug="bebidas")
        Product.objects.create(name="Agua", slug="agua", sku="AG01", base_price=100, category=cat)
        response = client.get(reverse('products:category', kwargs={'slug': 'bebidas'}))
        assert response.status_code == 200
        assert "Agua" in response.content.decode()

    def test_category_not_found(self, client):
        response = client.get(reverse('products:category', kwargs={'slug': 'no-existe'}))
        assert response.status_code == 404

@pytest.mark.django_db
class TestProductDetailView:
    def test_product_detail(self, client):
        cat = Category.objects.create(name="Bebidas", slug="bebidas")
        product = Product.objects.create(
            name="Agua", slug="agua", sku="AG01", base_price=100, category=cat, stock_quantity=10
        )
        response = client.get(reverse('products:product_detail', kwargs={'slug': 'agua'}))
        assert response.status_code == 200
        assert "Agua" in response.content.decode()
        assert "10" in response.content.decode()  # stock

    def test_inactive_product_404(self, client):
        cat = Category.objects.create(name="Bebidas", slug="bebidas")
        Product.objects.create(
            name="Agua", slug="agua", sku="AG01", base_price=100, category=cat, is_active=False
        )
        response = client.get(reverse('products:product_detail', kwargs={'slug': 'agua'}))
        assert response.status_code == 404

@pytest.mark.django_db
class TestSearchView:
    def test_search_finds_product(self, client):
        cat = Category.objects.create(name="Bebidas", slug="bebidas")
        Product.objects.create(name="Agua Mineral", slug="agua", sku="AG01", base_price=100, category=cat)
        response = client.get(reverse('products:search'), {'q': 'Agua'})
        assert response.status_code == 200
        assert "Agua Mineral" in response.content.decode()

    def test_search_no_results(self, client):
        response = client.get(reverse('products:search'), {'q': 'xyz123noexiste'})
        assert response.status_code == 200
        content = response.content.decode()
        assert "no" in content.lower() or "No" in content or "result" in content.lower()
