from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from product.models import Product


class Command(BaseCommand):
    help = '商品などの初期データをデータベースに投入します。'

    def handle(self, *args, **options):
        fixture_image_dir = settings.BASE_DIR / 'fixtures' / 'product_images'
        media_image_dir = settings.BASE_DIR / 'media' / 'product_image'

        Product.objects.all().delete()
        self._clear_media_product_images(media_image_dir)

        products_to_create = [
            {
                'name': '帆布トートバッグ',
                'price': 2800,
                'description': '港町の日常に合う、丈夫なトート',
                'image_name': 'tote_bag.png',
            },
            {
                'name': '港焙煎コーヒー豆',
                'price': 1500,
                'description': '朝の一杯用の中煎りブレンド',
                'image_name': 'coffee.png',
            },
            {
                'name': '海の恵みソルト',
                'price': 800,
                'description': '料理の仕上げに使える天然塩',
                'image_name': 'salt.png',
            },
            {
                'name': 'マリンキャップ',
                'price': 3200,
                'description': '日よけに使える定番キャップ',
                'image_name': 'cap.png',
            },
            {
                'name': 'オリジナル手ぬぐい',
                'price': 900,
                'description': '波と港のモチーフ入り',
                'image_name': 'tenugui.png',
            },
            {
                'name': 'ステンレスボトル',
                'price': 2400,
                'description': '保冷・保温対応の500ml',
                'image_name': 'bottle.png',
            },
            {
                'name': '港町クッキー詰め合わせ',
                'price': 1200,
                'description': '手土産にも使える6枚入り',
                'image_name': 'cookies.png',
            },
            {
                'name': '限定の陶器マグ（入荷待ち）',
                'price': 2000,
                'description': '次回入荷予定',
                'image_name': None,
            },
        ]

        created_count = 0
        for data in products_to_create:
            image_name = data['image_name']
            product = Product(
                name=data['name'],
                price=data['price'],
                description=data['description'],
            )

            if image_name:
                file_path = fixture_image_dir / image_name
                if file_path.exists():
                    with file_path.open('rb') as f:
                        product.image.save(image_name, File(f), save=False)
                else:
                    self.stdout.write(
                        self.style.WARNING(f'警告：画像ファイルが見つかりません - {file_path}')
                    )

            product.save()
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'{created_count}件の初期データの投入が完了しました！'))

    def _clear_media_product_images(self, media_image_dir):
        media_image_dir.mkdir(parents=True, exist_ok=True)
        for path in media_image_dir.iterdir():
            if path.is_file():
                path.unlink()
