from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_promotioncode'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_available',
            field=models.BooleanField(default=True, verbose_name='購入可能'),
        ),
    ]
