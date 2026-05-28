import io
import os
import random
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone

from offers.models import Offer
from products.models import Category, Product, ProductImage

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# Paleta de colores por categoria
CATEGORY_COLORS = {
    'Bebidas': ('#1E88E5', '#0D47A1'),
    'Gaseosas': ('#E53935', '#B71C1C'),
    'Bebidas alcoholicas': ('#8E24AA', '#4A148C'),
    'Alimentos': ('#43A047', '#1B5E20'),
    'Snacks': ('#FB8C00', '#E65100'),
    'Limpieza': ('#00ACC1', '#006064'),
}

DEFAULT_COLORS = ('#546E7A', '#263238')


def generate_product_image(name, category_name, sku):
    """Generate a product image with Pillow."""
    if not HAS_PIL:
        return None

    colors = CATEGORY_COLORS.get(category_name, DEFAULT_COLORS)
    bg_color, accent_color = colors

    img = Image.new('RGB', (400, 300), bg_color)
    draw = ImageDraw.Draw(img)

    # Decorative circle
    draw.ellipse([50, 20, 350, 270], fill=accent_color, outline=None)

    # Inner circle (lighter)
    r = (accent_color[0] if isinstance(accent_color, str) else '#333')
    lighter = bg_color  # fallback
    try:
        r_val = int(accent_color[1:3], 16)
        g_val = int(accent_color[3:5], 16)
        b_val = int(accent_color[5:7], 16)
        lighter = f'#{min(255, r_val + 40):02x}{min(255, g_val + 40):02x}{min(255, b_val + 40):02x}'
    except (ValueError, IndexError):
        lighter = accent_color
    draw.ellipse([100, 60, 300, 230], fill=lighter, outline=None)

    # Draw product name centered
    font_size = 16
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    # Word wrap
    words = name.split()
    lines = []
    current_line = ''
    for word in words:
        test_line = f'{current_line} {word}'.strip()
        try:
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
        except (AttributeError, TypeError):
            w = len(test_line) * 8
        if w > 340 and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    lines.append(current_line)

    y_start = 120 - (len(lines) * 10)
    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
        except (AttributeError, TypeError):
            tw = len(line) * 8
        x = (400 - tw) // 2
        draw.text((x, y_start), line, fill='white', font=font)
        y_start += 22

    # Save to in-memory file
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return ContentFile(buffer.read(), name=f'{slugify(name)}.png')


class Command(BaseCommand):
    help = 'Seed the database with sample data and product images'

    def handle(self, *args, **options):
        self.stdout.write('Creando categorías...')
        bebidas, _ = Category.objects.get_or_create(name='Bebidas', defaults={'slug': 'bebidas'})
        alimentos, _ = Category.objects.get_or_create(name='Alimentos', defaults={'slug': 'alimentos'})
        limpieza, _ = Category.objects.get_or_create(name='Limpieza', defaults={'slug': 'limpieza'})
        bebidas_alcoholicas, _ = Category.objects.get_or_create(
            name='Bebidas alcoholicas', parent=bebidas, defaults={'slug': 'bebidas-alcoholicas'}
        )
        gaseosas, _ = Category.objects.get_or_create(name='Gaseosas', parent=bebidas, defaults={'slug': 'gaseosas'})
        snacks, _ = Category.objects.get_or_create(name='Snacks', parent=alimentos, defaults={'slug': 'snacks'})

        self.stdout.write('Creando productos...')
        product_data = [
            ('Coca-Cola 2.25L', gaseosas, 1200.00, 150, 20),
            ('Sprite 2.25L', gaseosas, 1150.00, 120, 20),
            ('Fanta Naranja 2.25L', gaseosas, 1150.00, 100, 20),
            ('Cerveza Quilmes 1L', bebidas_alcoholicas, 1800.00, 80, 15),
            ('Cerveza Stella Artois 1L', bebidas_alcoholicas, 2200.00, 60, 15),
            ('Papas Lays Clasicas 200g', snacks, 1500.00, 90, 15),
            ('Papas Pringles 150g', snacks, 2500.00, 70, 15),
            ('Maní salado 500g', snacks, 900.00, 110, 15),
            ('Detergente Ala 1.5L', limpieza, 1300.00, 200, 25),
            ('Lavandina Ayudín 2L', limpieza, 850.00, 180, 25),
            ('Jabón en polvo Skip 3kg', limpieza, 4500.00, 50, 10),
            ('Esponja Scotch-Brite x3', limpieza, 650.00, 300, 30),
            ('Agua mineral Villa del Sur 2L', bebidas, 700.00, 250, 30),
            ('Jugo Baggio Naranja 1L', bebidas, 950.00, 140, 20),
            ('Chocolate Milka 100g', alimentos, 1200.00, 85, 15),
        ]

        featured_names = [
            'Coca-Cola 2.25L', 'Papas Lays Clasicas 200g',
            'Jabón en polvo Skip 3kg', 'Cerveza Stella Artois 1L',
        ]

        # First pass: create/update products without images
        products_created = 0
        for name, category, price, stock, threshold in product_data:
            if Product.objects.filter(name=name).exists():
                continue
            base_slug = slugify(name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            sku = slugify(name).replace('-', '')[:20].upper() + str(random.randint(10, 99))
            product = Product.objects.create(
                name=name,
                slug=slug,
                sku=sku,
                base_price=price,
                category=category,
                stock_quantity=stock,
                min_stock_threshold=threshold,
                is_active=True,
                is_featured=name in featured_names,
            )
            products_created += 1

            # Generate and attach image
            cat_name = category.name if not category.parent else f'{category.parent.name} > {category.name}'
            image_file = generate_product_image(name, category.name, sku)
            if image_file:
                ProductImage.objects.create(
                    product=product,
                    image=image_file,
                    is_primary=True,
                    alt_text=name,
                    order=0,
                )

        self.stdout.write(f'  {products_created} productos creados con imágenes.')

        # Mark featured (for existing products too)
        Product.objects.filter(name__in=featured_names).update(is_featured=True)

        self.stdout.write('Creando ofertas...')
        now = timezone.now()
        products = list(Product.objects.all())

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

        self.stdout.write(self.style.SUCCESS('✅ Datos de prueba creados correctamente con imágenes.'))
