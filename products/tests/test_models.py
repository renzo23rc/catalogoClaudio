import pytest
from django.db import IntegrityError
from products.models import Category, Product

@pytest.mark.django_db
class TestCategory:
    def test_create_root_category(self):
        cat = Category.objects.create(name="Bebidas", slug="bebidas")
        assert cat.name == "Bebidas"
        assert cat.slug == "bebidas"
        assert cat.parent is None
        assert str(cat) == "Bebidas"

    def test_create_subcategory(self):
        parent = Category.objects.create(name="Bebidas", slug="bebidas")
        child = Category.objects.create(name="Aguas", slug="aguas", parent=parent)
        assert child.parent == parent
        assert str(child) == "Bebidas > Aguas"
        assert list(parent.children.all()) == [child]

    def test_slug_auto_generation(self):
        cat = Category.objects.create(name="Productos de Limpieza")
        assert cat.slug == "productos-de-limpieza"

    def test_get_descendants(self):
        parent = Category.objects.create(name="Bebidas", slug="bebidas")
        child = Category.objects.create(name="Aguas", slug="aguas", parent=parent)
        grandchild = Category.objects.create(name="Con gas", slug="con-gas", parent=child)
        assert list(parent.get_descendants()) == [child, grandchild]

@pytest.mark.django_db
class TestProduct:
    def test_create_product(self):
        cat = Category.objects.create(name="Bebidas", slug="bebidas")
        product = Product.objects.create(
            name="Agua Mineral 500ml",
            slug="agua-mineral-500ml",
            sku="AM001",
            base_price=120.00,
            category=cat,
            stock_quantity=50,
        )
        assert product.name == "Agua Mineral 500ml"
        assert str(product) == "Agua Mineral 500ml"
        assert product.min_stock_threshold == 10  # default

    def test_unique_sku(self):
        cat = Category.objects.create(name="Bebidas", slug="bebidas")
        Product.objects.create(name="Prod A", slug="prod-a", sku="SKU001", base_price=100, category=cat)
        with pytest.raises(IntegrityError):
            Product.objects.create(name="Prod B", slug="prod-b", sku="SKU001", base_price=200, category=cat)

    def test_slug_auto_generation(self):
        cat = Category.objects.create(name="Bebidas", slug="bebidas")
        product = Product.objects.create(name="Agua Mineral", sku="AM999", base_price=100, category=cat)
        assert product.slug == "agua-mineral"
