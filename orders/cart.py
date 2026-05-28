class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product_id, quantity=1):
        product_id = str(product_id)
        if product_id in self.cart:
            self.cart[product_id] += quantity
        else:
            self.cart[product_id] = quantity
        self.save()

    def remove(self, product_id):
        if str(product_id) in self.cart:
            del self.cart[str(product_id)]
            self.save()

    def update(self, product_id, quantity):
        if quantity > 0:
            self.cart[str(product_id)] = quantity
        else:
            self.remove(product_id)
        self.save()

    def get_items(self):
        from products.models import Product
        ids = [int(k) for k in self.cart.keys()]
        products = Product.objects.filter(id__in=ids, is_active=True)
        items = []
        for product in products:
            qty = self.cart[str(product.id)]
            items.append({
                'product': product,
                'quantity': qty,
                'total': product.base_price * qty,
            })
        return items

    def get_total(self):
        return sum(item['total'] for item in self.get_items())

    def clear(self):
        self.session['cart'] = {}
        self.save()

    def save(self):
        self.session.modified = True

    def __len__(self):
        return sum(self.cart.values())
