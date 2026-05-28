import logging
import os
import re
import ssl
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Category, Product, ProductImage

logger = logging.getLogger(__name__)

AGCOM_URL = 'https://agcom.mdx.com.ar/ListaPrecios/index.jsp'

CATEGORY_SLUGS = {
    'ACEITES/CONDIMENTOS': 'aceites-condimentos',
    'ALMACEN': 'almacen',
    'APERITIVOS': 'aperitivos',
    'CERVEZAS': 'cervezas',
    'ENLATADOS/CONSERVAS': 'enlatados-conservas',
    'FRUTOS SECOS': 'frutos-secos',
    'GALLETITAS': 'galletitas',
    'GASEOSAS/JUGOS/AGUAS': 'gaseosas-jugos-aguas',
    'KIOSCO': 'kiosco',
    'PASTA SECA': 'pasta-seca',
    'PROD. LIMPIEZA': 'prod-limpieza',
    'PROMO': 'promo',
    'SNACKS': 'snacks',
    'VINOS/ESPUMANTES': 'vinos-espumantes',
    'YERBAS/INFUSIONES': 'yerbas-infusiones',
}

# Extractors (AGCOM HTML usa atributos sin comillas)
IMG = re.compile(r'<img src=([^ \t\r\n>]+)')
NAME = re.compile(r'product-title">\s*(.*?)\s*<br></p>')
PRICE = re.compile(r'price-tag">\$?([0-9.]+)</span>')
STOCK = re.compile(r'stock-tag">Quedan:\s*([0-9]+)\s*U</span>')
CAT_HDR = re.compile(r'<h2 class="m-0">([^<]+)</h2>')


class Command(BaseCommand):
    help = 'Importa todos los productos desde AGCOM'

    def add_arguments(self, parser):
        parser.add_argument('--url', default=AGCOM_URL)
        parser.add_argument('--no-images', action='store_true')

    def handle(self, *args, **options):
        url = options['url']
        download_images = not options.get('no_images', False)

        self.stdout.write(f'Obteniendo catálogo desde {url}...')
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
            })
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                html = resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            return

        # Extract all data in order
        names = NAME.findall(html)
        prices = PRICE.findall(html)
        stocks = STOCK.findall(html)

        # Deduplicate images (AGCOM HTML duplica cada producto: visible + comentado)
        all_images = IMG.findall(html)
        images = []
        seen = set()
        for url in all_images:
            if 'art/img' in url and url not in seen:
                seen.add(url)
                images.append(url)

        # Build category-position map: for each product, determine its category
        # based on which category header appears before it
        cat_positions = [(m.start(), m.group(1)) for m in CAT_HDR.finditer(html)]
        name_positions = [m.start() for m in NAME.finditer(html)]

        stats = {'cats': 0, 'prods': 0, 'imgs': 0}

        # Create categories
        for _, cname in cat_positions:
            slug = CATEGORY_SLUGS.get(cname, slugify(cname)[:50])
            cat, created = Category.objects.get_or_create(
                slug=slug, defaults={'name': cname, 'is_active': True}
            )
            if created:
                stats['cats'] += 1

        # Assign each product to a category based on page position
        # Iterate through products in order, tracking current category
        current_cat_idx = 0
        cat_list = [(cname, CATEGORY_SLUGS.get(cname, slugify(cname)[:50]))
                    for _, cname in cat_positions]

        for i, npos in enumerate(name_positions):
            # Advance category if this product is past the next category header
            while (current_cat_idx + 1 < len(cat_positions) and
                   npos > cat_positions[current_cat_idx + 1][0]):
                current_cat_idx += 1

            cname, cslug = cat_list[current_cat_idx]
            prod_name = names[i].strip() if i < len(names) else ''
            if not prod_name:
                continue

            # Parse fields
            price = round(float(prices[i].replace(',', '.')), 2) if i < len(prices) else 0.0
            stock = int(stocks[i]) if i < len(stocks) else 0

            # Match image by index (now deduplicated, 1:1 with products)
            img_url = images[i] if i < len(images) else ''

            # SKU from image URL
            sku_match = re.search(r'/(\d+)/(\d+)\.', img_url) if img_url else None
            sku = f"AG{sku_match.group(1)}{sku_match.group(2)}" if sku_match else \
                  slugify(prod_name).replace('-', '')[:20].upper()

            # Unique slug
            base = slugify(prod_name)[:50]
            slug = base
            c = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base}-{c}"
                c += 1

            category = Category.objects.get(slug=cslug)

            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': prod_name[:255],
                    'slug': slug,
                    'description': f'{prod_name}',
                    'base_price': price,
                    'category': category,
                    'stock_quantity': stock,
                    'is_active': True,
                }
            )
            if created:
                stats['prods'] += 1

            if download_images and img_url and not product.images.filter(is_primary=True).exists():
                self._download_image(product, img_url, stats)

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {stats["cats"]} categorías, {stats["prods"]} productos, {stats["imgs"]} imágenes'
        ))

    def _download_image(self, product, img_url, stats):
        try:
            ctx = ssl._create_unverified_context()
            data = urllib.request.urlopen(img_url, context=ctx, timeout=5).read()
            ext = os.path.splitext(img_url.split('/')[-1])[1] or '.png'
            fname = f"{slugify(product.name)[:40]}{ext}"
            ProductImage.objects.create(
                product=product,
                image=ContentFile(data, name=fname),
                is_primary=True,
                alt_text=product.name,
                order=0,
            )
            stats['imgs'] += 1
            if stats['imgs'] % 30 == 0:
                self.stdout.write(f'    📸 {stats["imgs"]} imágenes...')
        except Exception as e:
            logger.warning(f'Error imagen {product.name}: {e}')
