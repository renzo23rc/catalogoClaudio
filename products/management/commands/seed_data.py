import random

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from offers.models import Offer
from products.models import Category, Product


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creando categorias...')
        bebidas, _ = Category.objects.get_or_create(name='Bebidas', defaults={'slug': 'bebidas'})
        alimentos, _ = Category.objects.get_or_create(name='Alimentos', defaults={'slug': 'alimentos'})
        limpieza, _ = Category.objects.get_or_create(name='Limpieza', defaults={'slug': 'limpieza'})
        bebidas_alcoholicas, _ = Category.objects.get_or_create(name='Bebidas alcoholicas', parent=bebidas, defaults={'slug': 'bebidas-alcoholicas'})
        gaseosas, _ = Category.objects.get_or_create(name='Gaseosas', parent=bebidas, defaults={'slug': 'gaseosas'})
        snacks, _ = Category.objects.get_or_create(name='Snacks', parent=alimentos, defaults={'slug': 'snacks'})

        self.stdout.write('Creando productos...')
        product_data = [
            ('Coca-Cola 2.25L', gaseosas, 1200.00, 150),
            ('Sprite 2.25L', gaseosas, 1150.00, 120),
            ('Fanta Naranja 2.25L', gaseosas, 1150.00, 100),
            ('Cerveza Quilmes 1L', bebidas_alcoholicas, 1800.00, 80),
            ('Cerveza Stella Artois 1L', bebidas_alcoholicas, 2200.00, 60),
            ('Papas Lays Clasicas 200g', snacks, 1500.00, 90),
            ('Papas Pringles 150g', snacks, 2500.00, 70),
            ('Maní salado 500g', snacks, 900.00, 110),
            ('Detergente Ala 1.5L', limpieza, 1300.00, 200),
            ('Lavandina Ayudín 2L', limpieza, 850.00, 180),
            ('Jabón en polvo Skip 3kg', limpieza, 4500.00, 50),
            ('Esponja Scotch-Brite x3', limpieza, 650.00, 300),
            ('Agua mineral Villa del Sur 2L', bebidas, 700.00, 250),
            ('Jugo Baggio Naranja 1L', bebidas, 950.00, 140),
            ('Chocolate Milka 100g', alimentos, 1200.00, 85),
        ]

        products = []
        for name, category, price, stock in product_data:
            sku = slugify(name).replace('-', '')[:20].upper() + str(random.randint(10, 99))
            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'slug': slugify(name),
                    'base_price': price,
                    'category': category,
                    'stock_quantity': stock,
                    'is_active': True,
                }
            )
            if created:
                products.append(product)

        self.stdout.write(f'  {len(products)} productos creados.')

        self.stdout.write('Creando ofertas...')
        now = __import__('django.utils.timezone').utils.timezone.now()
        from datetime import timedelta
        if products:
            offer1, _ = Offer.objects.get_or_create(
                name='Descuento en gaseosas',
                defaults={
                    'discount_type': 'percentage',
                    'discount_value': 15,
                    'start_date': now,
                    'end_date': now + timedelta(days=30),
                    'is_active': True,
                }
            )
            offer1.products.set([p for p in products if p.category == gaseosas][:3])

            offer2, _ = Offer.objects.get_or_create(
                name='Oferta en limpieza',
                defaults={
                    'discount_type': 'fixed',
                    'discount_value': 300,
                    'start_date': now,
                    'end_date': now + timedelta(days=30),
                    'is_active': True,
                }
            )
            offer2.products.set([p for p in products if p.category == limpieza][:3])

        self.stdout.write(self.style.SUCCESS('Datos de prueba creados correctamente.'))
