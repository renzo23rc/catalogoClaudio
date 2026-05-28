import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'BORRA todo (DB + imágenes) y regenera desde cero'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='No pedir confirmación')

    def handle(self, *args, **options):
        if not options['force']:
            self.stdout.write(self.style.Warning('⚠️  ESTO BORRA TODO: productos, pedidos, ofertas e imágenes'))
            confirm = input('Escribí "SI" para confirmar: ')
            if confirm.strip().upper() != 'SI':
                self.stdout.write(self.style.WARNING('Cancelado.'))
                return

        # 1. Kill DB
        self.stdout.write('1/4 Eliminando base de datos...')
        db_path = settings.BASE_DIR / 'db.sqlite3'
        if db_path.exists():
            db_path.unlink()
            self.stdout.write('  ✅ db.sqlite3 eliminado')

        # 2. Clean media
        self.stdout.write('2/4 Borrando imágenes...')
        media_products = os.path.join(settings.MEDIA_ROOT, 'products')
        if os.path.exists(media_products):
            shutil.rmtree(media_products)
            self.stdout.write('  ✅ imágenes eliminadas')

        # 3. Fresh migrate
        self.stdout.write('3/4 Recreando tablas...')
        call_command('migrate')
        self.stdout.write('  ✅ tablas creadas')

        # 4. Seed
        self.stdout.write('4/4 Sembrando datos de prueba...')
        call_command('seed_data')

        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@catalogo.com', 'admin123')
            self.stdout.write('  ✅ usuario admin creado: admin / admin123')
        else:
            self.stdout.write('  ✅ usuario admin ya existe')

        self.stdout.write(self.style.SUCCESS('\n✅ TODO REGENERADO. Corre el servidor:'))
        self.stdout.write('   python manage.py runserver')
