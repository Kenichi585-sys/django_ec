import secrets
import string
from django.core.management.base import BaseCommand
from product.models import PromotionCode

class Command(BaseCommand):
    help = '10個のランダムなプロモーションコードを生成して一括保存します'

    def handle(self, *args, **options):
        all_chars = string.ascii_letters + string.digits
        
        promotion_codes_list = []
        
        for _ in range(10):
            generated_code = "".join(secrets.choice(all_chars) for _ in range(7))
            amount = secrets.randbelow(10) * 100 + 100 
            promotion_codes_list.append(
                PromotionCode(code=generated_code, discount_amount=amount)
            )

        PromotionCode.objects.bulk_create(promotion_codes_list)
        
        for p in promotion_codes_list:
            self.stdout.write(self.style.SUCCESS(f'生成完了: {p.code} (¥{p.discount_amount})'))

        self.stdout.write(self.style.SUCCESS(f'計{len(promotion_codes_list)}件をDBに一括保存しました。'))

