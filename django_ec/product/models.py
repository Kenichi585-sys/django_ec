from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(
        verbose_name='商品名',
        max_length=100,
    )
    description = models.CharField(
        verbose_name='商品説明',
        max_length=100,
        blank=True,
        null=True,
    )
    price = models.DecimalField(
        verbose_name='価格',
        max_digits=8,
        decimal_places=2,
    )
    image = models.ImageField(
        upload_to='product_image/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name_plural = '商品'

    def __str__(self):
        return self.name