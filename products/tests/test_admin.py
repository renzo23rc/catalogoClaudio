import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product

@pytest.mark.django_db
class TestProductAdmin:
    def test_admin_list_accessible(self, client):
        User.objects.create_superuser('admin', 'admin@test.com', 'pass')
        client.login(username='admin', password='pass')
        response = client.get(reverse('admin:products_product_changelist'))
        assert response.status_code == 200

    def test_admin_add_accessible(self, client):
        User.objects.create_superuser('admin', 'admin@test.com', 'pass')
        client.login(username='admin', password='pass')
        response = client.get(reverse('admin:products_product_add'))
        assert response.status_code == 200
