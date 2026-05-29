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

# Extraer cards individuales (cada card = 1 producto con su imagen)
CARD_RE = re.compile(
    r'<div class="card product-card shadow-sm">(.*?)</div>\s*</div>',
    re.DOTALL
)

# Extractores dentro de cada card
IMG_RE = re.compile(r'<img src=([^ \t\r\n>]+)')
NAME_RE = re.compile(r'product-title">\s*(.*?)\s*<br></p>')
PRICE_RE = re.compile(r'price-tag">\$?([0-9.]+)</span>')
STOCK_RE = re.compile(r'stock-tag">Quedan:\s*([0-9]+)\s*U</span>')


def parse_ars_price(text):
    """Convierte precio argentino a float.
    $2.412 -> 2412.0  (punto = miles)
    $1.500,50 -> 1500.50  (punto = miles, coma = decimal)
    """
    text = text.strip()
    if not text:
        return 0.0
    # Si tiene coma, es decimal ARS
    if ',' in text:
        text = text.replace('.', '')   # saca miles
        text = text.replace(',', '.')  # coma -> punto decimal
    else:
        text = text.replace('.', '')   # solo miles
    try:
        return round(float(text), 2)
    except ValueError:
        return 0.0


class Command(BaseCommand):
    help = 'Importa todos los productos desde AGCOM'

    def add_arguments(self, parser):
        parser.add_argument('--url', default=AGCOM_URL)
        parser.add_argument('--no-images', action='store_true')
        parser.add_argument('--only-images', action='store_true',
                            help='Solo descargar imágenes faltantes')

    def handle(self, *args, **options):
        url = options['url']
        download_images = not options['no_images']
        only_images = options.get('only_images', False)

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

        # Extraer categorías con sus posiciones
        cat_headers = list(re.finditer(
            r'<h2 class="m-0">([^<]+)</h2>', html
        ))

        if not cat_headers:
            self.stdout.write(self.style.ERROR('No se encontraron categorías'))
            return

        if not only_images:
            # Crear categorías
            for m in cat_headers:
                cname = m.group(1).strip()
                slug = CATEGORY_SLUGS.get(cname, slugify(cname)[:50])
                Category.objects.get_or_create(
                    slug=slug, defaults={'name': cname, 'is_active': True}
                )
            self.stdout.write(f'✅ {len(cat_headers)} categorías')

            # Extraer todas las cards de productos
            cards = list(CARD_RE.finditer(html))
            self.stdout.write(f'Cards encontradas: {len(cards)}')

        # Extraer cards y asignar a categorías por posición
        cards_data = []
        for card_match in CARD_RE.finditer(html):
            card_html = card_match.group(1)
            card_pos = card_match.start()

            # Asignar categoría: la última cuyo header esté antes de esta card
            cat_name = cat_headers[0].group(1).strip()
            for h in cat_headers:
                if h.start() < card_pos:
                    cat_name = h.group(1).strip()
                else:
                    break

            # Extraer datos
            img_match = IMG_RE.search(card_html)
            name_match = NAME_RE.search(card_html)
            price_match = PRICE_RE.search(card_html)
            stock_match = STOCK_RE.search(card_html)

            if not name_match:
                continue

            img_url = img_match.group(1) if img_match else ''
            prod_name = name_match.group(1).strip()
            price = parse_ars_price(price_match.group(1)) if price_match else 0.0
            stock = int(stock_match.group(1)) if stock_match else 0

            cards_data.append({
                'name': prod_name,
                'price': price,
                'stock': stock,
                'img_url': img_url,
                'category': cat_name,
            })

        self.stdout.write(f'Productos parseados: {len(cards_data)}')

        stats = {'prods': 0, 'imgs': 0}

        for prod in cards_data:
            cat_slug = CATEGORY_SLUGS.get(prod['category'], slugify(prod['category'])[:50])
            try:
                category = Category.objects.get(slug=cat_slug)
            except Category.DoesNotExist:
                continue

            # SKU desde URL de imagen
            sku_match = re.search(r'/(\d+)/(\d+)\.', prod['img_url']) if prod['img_url'] else None
            sku = f"AG{sku_match.group(1)}{sku_match.group(2)}" if sku_match else \
                  slugify(prod['name']).replace('-', '')[:20].upper()

            # Slug único
            base = slugify(prod['name'])[:50]
            slug = base
            c = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base}-{c}"
                c += 1

            if not only_images:
                product, created = Product.objects.get_or_create(
                    sku=sku,
                    defaults={
                        'name': prod['name'][:255],
                        'slug': slug,
                        'base_price': prod['price'],
                        'category': category,
                        'stock_quantity': prod['stock'],
                        'is_active': True,
                    }
                )
                if created:
                    stats['prods'] += 1
            else:
                try:
                    product = Product.objects.get(sku=sku)
                except Product.DoesNotExist:
                    continue

            # Descargar imagen si no tiene
            if download_images and prod['img_url'] and not product.images.filter(is_primary=True).exists():
                self._download_image(product, prod['img_url'], stats)

        if not only_images:
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ {len(cat_headers)} categorías, {stats["prods"]} productos nuevos'
            ))

        if download_images:
            total = Product.objects.filter(images__is_primary=True).count()
            self.stdout.write(self.style.SUCCESS(
                f'📸 {stats["imgs"]} descargadas esta ronda | '
                f'{total}/{Product.objects.count()} productos con imagen'
            ))

    def _download_image(self, product, img_url, stats):
        try:
            from PIL import Image as PILImage
            import io as _io

            ctx = ssl._create_unverified_context()
            data = urllib.request.urlopen(img_url, context=ctx, timeout=5).read()

            # Normalize to 400x300
            img = PILImage.open(_io.BytesIO(data))
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGBA')
                bg = PILImage.new('RGBA', img.size, (245, 245, 245, 255))
                bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                img = bg.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            img.thumbnail((400, 300), PILImage.LANCZOS)
            canvas = PILImage.new('RGB', (400, 300), (245, 245, 245))
            x = (400 - img.width) // 2
            y = (300 - img.height) // 2
            canvas.paste(img, (x, y))

            buf = _io.BytesIO()
            canvas.save(buf, format='JPEG', quality=85)
            buf.seek(0)

            fname = f"{slugify(product.name)[:40]}.jpg"
            ProductImage.objects.create(
                product=product,
                image=ContentFile(buf.read(), name=fname),
                is_primary=True,
                alt_text=product.name,
                order=0,
            )
            stats['imgs'] += 1
            if stats['imgs'] % 30 == 0:
                self.stdout.write(f'    📸 {stats["imgs"]}...')
        except Exception as e:
            logger.warning(f'Error {product.name[:30]}: {e}')
