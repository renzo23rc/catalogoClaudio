import pytest
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from products.models import Category, Product
from offers.models import Offer

@pytest.mark.django_db
class TestOffer:
    @pytest.fixture
    def product(self):
        cat = Category.objects.create(name="Test", slug="test")
        return Product.objects.create(
            name="Producto Test", slug="test-p", sku="TST01",
            base_price=Decimal('100.00'), category=cat
        )

    @pytest.fixture
    def active_offer(self, product):
        now = timezone.now()
        offer = Offer.objects.create(
            name="10% Off",
            discount_type='percentage',
            discount_value=10,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7),
        )
        offer.products.add(product)
        return offer

    def test_percentage_discount(self, product, active_offer):
        discounted = active_offer.get_discounted_price(product)
        assert discounted == Decimal('90.00')

    def test_fixed_discount(self, product):
        now = timezone.now()
        offer = Offer.objects.create(
            name="$15 Off",
            discount_type='fixed',
            discount_value=Decimal('15.00'),
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7),
        )
        offer.products.add(product)
        discounted = offer.get_discounted_price(product)
        assert discounted == Decimal('85.00')

    def test_fixed_discount_floor(self, product):
        now = timezone.now()
        offer = Offer.objects.create(
            name="$200 Off",
            discount_type='fixed',
            discount_value=Decimal('200.00'),
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7),
        )
        offer.products.add(product)
        discounted = offer.get_discounted_price(product)
        assert discounted == Decimal('0.00')

    def test_is_currently_active(self, active_offer):
        assert active_offer.is_currently_active is True

    def test_future_offer_inactive(self):
        now = timezone.now()
        offer = Offer.objects.create(
            name="Future Offer",
            discount_type='percentage',
            discount_value=10,
            start_date=now + timedelta(days=30),
            end_date=now + timedelta(days=60),
        )
        assert offer.is_currently_active is False
