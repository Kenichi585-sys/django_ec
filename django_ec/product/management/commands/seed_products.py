from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.base import ContentFile
from pathlib import  Path
from product.models import Product
import os
import tempfile

class Command(BaseCommand):
    help = '商品などの初期データをデータベースに投入します。'

    def handle(self, *args, **options):
        Product.objects.all().delete()

        image_dir = settings.BASE_DIR / 'media' / 'product_image'

        products_to_create = [
            {'name': 'Tシャツ', 'price': 1500, 'description': '定番のTシャツ', 'image_name': 'tshirt.png'},
            {'name': 'デニムパンツ', 'price': 5000, 'description': '定番のストレートデニム。', 'image_name': 'denim.png'},
            {'name': 'トートバッグ', 'price': 2000, 'description': '大容量トートバッグ', 'image_name': 'tote.png'},
            {'name': 'カレンダー', 'price': 500, 'description': '2026年のカレンダー', 'image_name': 'calendar.png'},
            {'name': 'キャップ', 'price': 4000, 'description': '普通のキャップ', 'image_name': 'cap.png'},
            {'name': '靴', 'price': 10000, 'description': 'NIKEの靴', 'image_name': 'shoes.png'},
            {'name': 'ティッシュ', 'price': 200, 'description': '普通のティッシュ', 'image_name': 'tissue.jpg'},
            {'name': '水', 'price': 100, 'description': '天然水', 'image_name': 'mizu.jpg'},
        ]

        created_count = 0
        for data in products_to_create:
            file_name = data['image_name']
            file_path = image_dir / file_name

            if not file_path.exists():
                self.stdout.write(self.style.WARNING(f"警告：画像ファイルが見つかりません - {file_path}"))

            product = Product(
                name=data['name'],
                price=data['price'],
                description=data['description']
            )

            with file_path.open('rb') as f:
                django_file = File(f)

                product.image.save(file_name, django_file)

            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'{created_count}件の初期データの投入が完了しました！'))
    
