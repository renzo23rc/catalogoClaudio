import logging
import os
import re
import ssl
import time
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Product, ProductImage

logger = logging.getLogger(__name__)

AGCOM_URL = 'https://agcom.mdx.com.ar/ListaPrecios/index.jsp'
IMG_RE = re.compile(r'<img src=([^ \t\r\n>]+)')
NAME_RE = re.compile(r'product-title">\s*(.*?)\s*<br></p>')


class Command(BaseCommand):
    help = 'Descarga imágenes de AGCOM para productos existentes'

    def handle(self, *args, **options):
        # Fetch page to get image URLs
        self.stdout.write('Obteniendo catálogo AGCOM...')
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(AGCOM_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                html = resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            return

        # Extract names and images
        names = NAME_RE.findall(html)
        all_imgs = IMG_RE.findall(html)

        # Deduplicate images
        images = []
        seen = set()
        for url in all_imgs:
            if 'art/img' in url and url not in seen:
                seen.add(url)
                images.append(url)

        # Match products to images
        products_no_img = Product.objects.filter(images__isnull=True) | \
                          Product.objects.exclude(images__is_primary=True)
        products_no_img = products_no_img.distinct()

        self.stdout.write(f'{len(products_no_img)} productos sin imagen principal')
        self.stdout.write(f'{len(images)} imágenes disponibles en AGCOM')

        downloaded = 0
        failed = 0

        for product in products_no_img:
            if product.images.filter(is_primary=True).exists():
                continue

            # Find matching image by name
            best_url = ''
            best_score = 0
            prod_slug = slugify(product.name)

            for url in images:
                # Extract product code from URL
                url_code = re.search(r'/img//(\d+)/(\d+)', url)
                if not url_code:
                    continue
                img_name = f"{url_code.group(1)}{url_code.group(2)}"

                # Match by SKU
                if img_name in product.sku:
                    best_url = url
                    best_score = 999
                    break

                # Match by name similarity
                url_slug = slugify(url)
                score = 0
                # Count matching words
                for word in prod_slug.split('-'):
                    if len(word) > 2 and word in url_slug:
                        score += 1
                if score > best_score:
                    best_score = score
                    best_url = url

            if not best_url:
                failed += 1
                continue

            # Download
            try:
                ctx = ssl._create_unverified_context()
                time.sleep(0.3)  # Be nice to server
                data = urllib.request.urlopen(best_url, context=ctx, timeout=10).read()
                ext = os.path.splitext(best_url.split('/')[-1])[1] or '.png'
                fname = f"{slugify(product.name)[:40]}{ext}"

                ProductImage.objects.create(
                    product=product,
                    image=ContentFile(data, name=fname),
                    is_primary=True,
                    alt_text=product.name,
                    order=0,
                )
                downloaded += 1
                if downloaded % 20 == 0:
                    self.stdout.write(f'  📸 {downloaded} imágenes...')

            except Exception as e:
                failed += 1
                if failed <= 5:
                    logger.warning(f'Error {product.name}: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {downloaded} imágenes descargadas, {failed} fallaron'
        ))
