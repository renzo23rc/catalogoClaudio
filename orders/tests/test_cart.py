import pytest
from django.http import HttpRequest
from orders.cart import Cart

@pytest.fixture
def cart_request():
    request = HttpRequest()
    request.session = {}
    return request

class TestCart:
    def test_empty_cart(self, cart_request):
        cart = Cart(cart_request)
        assert len(cart) == 0
        assert cart.get_items() == []
        assert cart.get_total() == 0

    def test_add_item(self, cart_request):
        cart = Cart(cart_request)
        cart.add(1, 2)
        assert len(cart) == 2
        assert cart.cart == {'1': 2}

    def test_add_existing_item(self, cart_request):
        cart = Cart(cart_request)
        cart.add(1, 2)
        cart.add(1, 3)
        assert cart.cart == {'1': 5}

    def test_remove_item(self, cart_request):
        cart = Cart(cart_request)
        cart.add(1, 2)
        cart.remove(1)
        assert len(cart) == 0

    def test_update_quantity(self, cart_request):
        cart = Cart(cart_request)
        cart.add(1, 2)
        cart.update(1, 5)
        assert cart.cart == {'1': 5}

    def test_update_to_zero_removes(self, cart_request):
        cart = Cart(cart_request)
        cart.add(1, 2)
        cart.update(1, 0)
        assert len(cart) == 0

    def test_clear(self, cart_request):
        cart = Cart(cart_request)
        cart.add(1, 2)
        cart.add(2, 3)
        cart.clear()
        assert len(cart) == 0
