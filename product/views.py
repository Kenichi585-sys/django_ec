import base64
from typing import Tuple, Optional

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db.models import F
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from .models import Product, Cart, CartItem, Order, OrderItem, PromotionCode
from .forms import OrderForm


def get_cart_from_request(request, create_if_missing: bool = False) -> Tuple[Optional[Cart], bool]:
    """
    セッション上の cart_id から Cart を取得する補助関数。
    - create_if_missing=True の場合、見つからなければ新規作成して返す
    - 戻り値は (cart, is_not_found)
      - cart: Cart または None（create_if_missing=False で見つからないとき）
      - is_not_found: 取得できなかった（新規作成した/Noneだった）かどうかのフラグ
    """
    cart_id = request.session.get('cart_id')
    cart = None

    if cart_id:
        cart = Cart.objects.filter(pk=cart_id).first()

    if cart is None:
        if create_if_missing:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.pk
        return cart, True

    return cart, False


def basic_auth_required(func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if auth_header:
            auth_type, auth_string = auth_header.split(' ', 1)
            auth_decoded = base64.b64decode(auth_string).decode('utf-8')
            username, password = auth_decoded.split(':', 1)

            if username == 'admin' and password == 'pw':
                return func(request, *args, **kwargs)
            
        response = HttpResponse("Unauthorized", status=401)
        response['WWW-Authenticate'] = 'Basic realm="Main"'
        return response
    
    return wrapper
    

class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product/product_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        related_products = Product.objects.all().order_by('-pk')[:4]
        context['related_products'] = related_products
        return context
    

class CartView(View):
    def get(self, request):
        cart, is_not_found = get_cart_from_request(request, create_if_missing=False)
        
        cart_items = []
        total_price = 0
        cart_count = 0
        
        if is_not_found:
            if request.session.get('cart_id'):
                messages.warning(request, "長期間操作がなかったため、カートの情報が更新されました。")
        else:
            cart_items = cart.cart_items.select_related('product').all()
            total_price = sum(item.subtotal for item in cart_items)
            cart_count = sum(item.quantity for item in cart_items)

        applied_code = request.session.get('applied_promo')
        discount_amount = 0

        if applied_code:
            try:
                promo = PromotionCode.objects.get(code=applied_code, is_used=False)
                discount_amount = promo.discount_amount
            except:
                request.session.pop('applied_promo', None)

        discounted_total = max(0, total_price - discount_amount)

        form = OrderForm()
        return render(request, 'product/cart.html', {
            'cart_items': cart_items, 
            'total_price': total_price,
            'discount_amount': discount_amount,
            'discounted_total': discounted_total,
            'cart_count': cart_count,
            'form': form
        })
    

class CartAddView(View):
    def post(self, request, pk):
        product = Product.objects.get(pk=pk)
        quantity = int(request.POST.get('quantity', 1))

        cart, _ = get_cart_from_request(request, create_if_missing=True)

        cart_item, created = CartItem.objects.update_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity} if not CartItem.objects.filter(cart=cart, product=product).exists() 
                        else {'quantity': F('quantity') + quantity}
        )
        
        messages.success(request, mark_safe(f'{product.name}をカートに追加しました。'))

        next_page = request.POST.get('next')
        if next_page == 'product_detail':
            return redirect('product:product_detail', pk=pk)
        return redirect('product:cart_detail' if next_page else 'product:product_list')


class CartDeleteView(View):
    def post(self, request, pk):
        cart, is_not_found = get_cart_from_request(request)
        
        if is_not_found:
            return redirect('product:cart_detail')

        product = Product.objects.get(pk=pk)
        cart.cart_items.filter(product_id=pk).delete()

        messages.info(request, f'{product.name}をカートから削除しました')
        return redirect('product:cart_detail')


class CartDecreaseView(View):
    def post(self, request, pk):
        cart, is_not_found = get_cart_from_request(request)
        if is_not_found:
            return redirect('product:cart_detail')

        cart_item = cart.cart_items.filter(product_id=pk).first()
        
        if cart_item:
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                cart_item.delete()
            else:
                cart_item.save()

        return redirect('product:cart_detail')


@method_decorator(basic_auth_required, name='dispatch')
class ProductCreateView(CreateView):
    model = Product
    fields = ['name', 'description', 'price', 'image']
    template_name = 'product/product_create.html'
    success_url = reverse_lazy('product:manage_list')


@method_decorator(basic_auth_required, name='dispatch')
class ProductUpdateView(UpdateView):
    model = Product
    fields = ['name', 'description', 'price', 'image']
    template_name = 'product/product_update.html'
    success_url = reverse_lazy('product:manage_list')


@method_decorator(basic_auth_required, name='dispatch')
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product/product_delete.html'
    success_url = reverse_lazy('product:manage_list')


@method_decorator(basic_auth_required, name='dispatch')
class ProductManageListView(ListView):
    model = Product
    template_name = 'product/product_manage_list.html'
    context_object_name = 'manage_list'


@method_decorator(basic_auth_required, name='dispatch')
class OrderListView(ListView):
    model = Order
    template_name = 'product/order_list.html'
    context_object_name = 'orders'
    ordering = ['-created_at']


def order_create(request):
    cart, is_not_found = get_cart_from_request(request)

    if request.method == 'GET':
        if not cart or not cart.cart_items.exists():
            return redirect('product:product_list')
        form = OrderForm()
        return render(request, 'product/cart.html', {'form': form})

    if request.method == 'POST':
        if not cart or not cart.cart_items.exists():
            messages.error(request, "カートが空です。")
            return redirect('product:product_list')
        
        form = OrderForm(request.POST)

        if form.is_valid():
            applied_code = request.session.get('applied_promo')
            discount = 0
            promo_obj = None
            
            if applied_code:
                try:
                    promo_obj = PromotionCode.objects.get(code=applied_code, is_used=False)
                    discount = promo_obj.discount_amount
                except:
                    messages.error(request, "適用していたクーポンが無効、または既に使用されています。")
                    request.session.pop('applied_promo', None)
                    return redirect('product:cart_detail')

            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    total = cart.get_total_price() - discount
                    order.total_price = max(0, total)
                    order.status = 'paid'         
                    order.save()
                    
                    if promo_obj:
                        promo_obj.is_used = True
                        promo_obj.save()
                        request.session.pop('applied_promo', None)
                            
                    for item in cart.cart_items.all():
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            product_name=item.product.name,
                            product_price=item.product.price,
                            quantity=item.quantity
                        )
                        
                    cart.cart_items.all().delete()

            except Exception as e:
                    messages.error(request, "注文処理時にエラーが発生しました。")
                    return redirect('product:cart_detail')

            subject = "ご購入ありがとうございます"
            message = f"{order.last_name} {order.first_name} 様\n\nご購入ありがとうございます。\n合計金額: ¥{order.total_price:,.0f}\n住所: {order.address}\n\nまたのご利用をお待ちしております。"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [order.email]

            try:
                send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                print(f"メール送信エラー: {e}")
            
            messages.success(request, "ご購入ありがとうございます。")
            return redirect('product:product_list')
        
        messages.error(request, "入力内容に不備があります。")
        return render(request, 'product/cart.html', {
            'form': form,
            'cart_items': cart.cart_items.all(),
            'total_price': cart.get_total_price(),
        })
    form =OrderForm()
    return render(request, 'product/cart.html', {'form': form})


def apply_coupon(request):
    if request.method == 'POST':
        code_str = request.POST.get('promo_code', '').strip()

        if request.session.get('applied_promo') == code_str:
            messages.info(request, "そのコードはすでに適用されています。")
            return redirect('product:cart_detail')

        try:
            promo = PromotionCode.objects.get(code=code_str, is_used=False)
            request.session['applied_promo'] = code_str
            messages.success(request, f"クーポン「{code_str}」を適用しました。")

        except PromotionCode.DoesNotExist:
            messages.error(request, "無効なコード、または既に使用されています。")
            request.session.pop('applied_promo', None)

    return redirect('product:cart_detail')


