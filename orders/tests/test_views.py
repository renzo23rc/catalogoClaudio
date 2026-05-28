import pytest
from django.urls import reverse
from products.models import Category, Product

@pytest.mark.django_db
class TestCartViews:
    def test_cart_page_empty(self, client):
        response = client.get(reverse('orders:cart'))
        assert response.status_code == 200
        assert "vacio" in response.content.decode().lower()

    def test_add_to_cart(self, client):
        cat = Category.objects.create(name="Test", slug="test")
        product = Product.objects.create(
            name="Test Product", slug="test-p", sku="TST01", base_price=100, category=cat
        )
        response = client.get(reverse('orders:add_to_cart', kwargs={'product_id': product.id}))
        assert response.status_code == 302  # redirect

    def test_checkout_get(self, client):
        cat = Category.objects.create(name="Test", slug="test")
        product = Product.objects.create(
            name="Test Product", slug="test-p", sku="TST01", base_price=100, category=cat
        )
        session = client.session
        session['cart'] = {str(product.id): 2}
        session.save()
        response = client.get(reverse('orders:checkout'))
        assert response.status_code == 200

    def test_checkout_post_empty_cart(self, client):
        response = client.post(reverse('orders:checkout'), {
            'client_name': 'Test',
            'client_phone': '123456789',
            'client_email': 'test@test.com',
        })
        # Should redirect back or show error for empty cart
        assert response.status_code in [200, 302]
