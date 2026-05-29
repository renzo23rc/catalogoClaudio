import io
import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from products.models import ProductImage

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

WIDTH = 400
HEIGHT = 300


def resize_image(image_path):
    """Redimensiona una imagen a WIDTH x HEIGHT manteniendo aspecto, con padding."""
    img = Image.open(image_path)
    original_mode = img.mode

    # Convert to RGB if needed
    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGBA')
        background = Image.new('RGBA', img.size, (245, 245, 245, 255))
        background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
        img = background.convert('RGB')
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Calculate new size maintaining aspect ratio
    img.thumbnail((WIDTH, HEIGHT), Image.LANCZOS)

    # Create canvas and paste centered
    canvas = Image.new('RGB', (WIDTH, HEIGHT), (255, 255, 255))
    x = (WIDTH - img.width) // 2
    y = (HEIGHT - img.height) // 2
    canvas.paste(img, (x, y))

    buffer = io.BytesIO()
    canvas.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)

    new_name = os.path.splitext(os.path.basename(image_path))[0] + '.jpg'
    return ContentFile(buffer.read(), name=new_name)


class Command(BaseCommand):
    help = 'Normaliza todas las imágenes de productos a 400x300'

    def handle(self, *args, **options):
        if not HAS_PIL:
            self.stdout.write(self.style.ERROR('Pillow no está instalado. Corré: pip install Pillow'))
            return

        total = ProductImage.objects.filter(is_primary=True).count()
        self.stdout.write(f'Normalizando {total} imágenes a {WIDTH}x{HEIGHT}...')

        done = 0
        for pi in ProductImage.objects.filter(is_primary=True).select_related('product'):
            try:
                path = pi.image.path
                if not os.path.exists(path):
                    self.stdout.write(self.style.WARNING(f'  No encontrada: {path}'))
                    continue

                new_file = resize_image(path)
                pi.image.save(new_file.name, new_file, save=True)
                done += 1

                if done % 50 == 0:
                    self.stdout.write(f'  {done}/{total}...')

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Error {pi.product.name[:30]}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ {done} imágenes normalizadas a {WIDTH}x{HEIGHT}'))
