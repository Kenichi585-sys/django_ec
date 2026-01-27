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
    

class Cart(models.Model):
    created_at = models.DateTimeField(
        verbose_name='カゴに追加した日時',
        auto_now_add=True,
    )

    def get_total_price(self):
        return sum(item.subtotal for item in self.cart_items.all())
    


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE,
        related_name='cart_items'
        )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        verbose_name='数量',
    )

    @property
    def subtotal(self):
        return self.product.price * self.quantity
    
    def __str__(self):
        return self.product.name
        

class Order(models.Model):
    STATUS_CHOICES = [('pending', '支払い待ち'), ('paid', '支払いずみ')]

    last_name = models.CharField(max_length=50, verbose_name='姓')
    first_name = models.CharField(max_length=50, verbose_name='名')
    username = models.CharField(max_length=50, verbose_name='ユーザー名')
    email = models.EmailField(blank=True, verbose_name='メールアドレス')
    address = models.CharField(max_length=250, verbose_name='住所')
    card_name = models.CharField(max_length=100, verbose_name='カード名義', blank=True)
    card_number = models.CharField(max_length=16, verbose_name='カード番号', blank=True)
    card_expiry = models.CharField(max_length=5, verbose_name='有効期限', blank=True)

    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='合計金額')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='注文日時')

    class Meta:
        verbose_name = '注文'
        verbose_name_plural = '注文'

    def __str__(self):
        return f"注文ID: {self.id} - {self.last_name}"
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)

    product_name = models.CharField(max_length=100)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = '注文詳細'
        verbose_name_plural = '注文詳細'

    def __str__(self):
        return f"{self.product_name} (注文ID: {self.order.id})"
