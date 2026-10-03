from django.db import migrations, models


def mark_existing_orders_as_paid(apps, schema_editor):
    Order = apps.get_model('product', 'Order')
    Order.objects.filter(status='ordered').update(status='paid')


def mark_paid_orders_as_ordered(apps, schema_editor):
    Order = apps.get_model('product', 'Order')
    Order.objects.filter(status='paid').update(status='ordered')


class Migration(migrations.Migration):
    dependencies = [
        ('product', '0013_remove_order_card_expiry_remove_order_card_name_and_more'),
    ]

    operations = [
        migrations.RunPython(
            mark_existing_orders_as_paid,
            reverse_code=mark_paid_orders_as_ordered,
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', '支払い待ち'),
                    ('paid', '支払い済み（疑似決済）'),
                ],
                default='pending',
                max_length=10,
            ),
        ),
    ]
