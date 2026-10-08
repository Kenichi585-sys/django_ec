import base64
import logging
from typing import Tuple, Optional

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db.models import F
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction, IntegrityError, OperationalError

from .models import Product, Cart, CartItem, Order, OrderItem, PromotionCode
from .forms import OrderForm

logger = logging.getLogger(__name__)


def fetch_unused_promotion(code: Optional[str]) -> Optional[PromotionCode]:
    if not code:
        return None
    try:
        return PromotionCode.objects.get(code=code, is_used=False)
    except PromotionCode.DoesNotExist:
        return None


def redirect_after_cart_add(request, product_pk):
    next_page = request.POST.get('next')
    if next_page == 'product_detail':
        return redirect('product:product_detail', pk=product_pk)
    if next_page:
        return redirect('product:cart_detail')
    return redirect('product:product_list')


def send_order_confirmation_email(order) -> bool:
    subject = "ご購入ありがとうございます"
    message = (
        f"{order.last_name} {order.first_name} 様\n\n"
        f"ご購入ありがとうございます。\n"
        f"合計金額: ¥{order.total_price:,.0f}\n"
        f"住所: {order.address}\n\n"
        f"またのご利用をお待ちしております。"
    )
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [order.email])
        return True
    except Exception as e:
        logger.error(f"メール送信エラー: {e}")
        return False


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


def build_cart_page_context(request, cart, form=None):
    if form is None:
        form = OrderForm()

    if cart is None:
        return {
            'cart_items': [],
            'total_price': 0,
            'discount_amount': 0,
            'discounted_total': 0,
            'cart_count': 0,
            'form': form,
        }

    cart_items = cart.cart_items.select_related('product').all()
    total_price = sum(item.subtotal for item in cart_items)
    cart_count = sum(item.quantity for item in cart_items)

    applied_code = request.session.get('applied_promo')
    promo = fetch_unused_promotion(applied_code)
    if applied_code and promo is None:
        request.session.pop('applied_promo', None)
    discount_amount = promo.discount_amount if promo else 0

    discounted_total = max(0, total_price - discount_amount)

    return {
        'cart_items': cart_items,
        'total_price': total_price,
        'discount_amount': discount_amount,
        'discounted_total': discounted_total,
        'cart_count': cart_count,
        'form': form,
    }


def basic_auth_required(func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if auth_header:
            try:
                auth_type, auth_string = auth_header.split(' ', 1)
                if auth_type.lower() != 'basic':
                    raise ValueError('Unsupported authorization scheme')
                auth_decoded = base64.b64decode(auth_string).decode('utf-8')
                username, password = auth_decoded.split(':', 1)
            except (ValueError, Exception):
                pass
            else:
                if (
                    settings.BASIC_AUTH_USERNAME
                    and settings.BASIC_AUTH_PASSWORD
                    and username == settings.BASIC_AUTH_USERNAME
                    and password == settings.BASIC_AUTH_PASSWORD
                ):
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
        related_products = Product.objects.exclude(pk=self.object.pk).order_by('-pk')[:4]
        context['related_products'] = related_products
        return context
    

class CartView(View):
    def get(self, request):
        cart, is_not_found = get_cart_from_request(request, create_if_missing=False)

        if is_not_found and request.session.get('cart_id'):
            messages.warning(request, "長期間操作がなかったため、カートの情報が更新されました。")

        context = build_cart_page_context(
            request,
            None if is_not_found else cart,
        )
        return render(request, 'product/cart.html', context)
    

class CartAddView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

        if not product.is_available:
            messages.warning(request, f'{product.name}は現在ご購入いただけません。')
            return redirect_after_cart_add(request, pk)

        quantity = int(request.POST.get('quantity', 1))

        cart, _ = get_cart_from_request(request, create_if_missing=True)

        CartItem.objects.update_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
            if not CartItem.objects.filter(
                cart=cart,
                product=product
            ).exists()
            else {'quantity': F('quantity') + quantity}
        )
        
        messages.success(request, mark_safe(f'{product.name}をカートに追加しました。'))
        return redirect_after_cart_add(request, pk)


class CartDeleteView(View):
    def post(self, request, pk):
        cart, is_not_found = get_cart_from_request(request)
        
        if is_not_found:
            return redirect('product:cart_detail')

        product = get_object_or_404(Product, pk=pk)
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
        return render(request, 'product/cart.html', build_cart_page_context(request, cart))

    if request.method == 'POST':
        if not cart or not cart.cart_items.exists():
            messages.error(request, "カートが空です。")
            return redirect('product:product_list')
        
        form = OrderForm(request.POST)

        if form.is_valid():
            applied_code = request.session.get('applied_promo')
            promo_obj = fetch_unused_promotion(applied_code)
            discount = promo_obj.discount_amount if promo_obj else 0

            if applied_code and promo_obj is None:
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

            except IntegrityError:
                messages.error(request, "注文の保存に失敗しました。入力内容を確認のうえ、もう一度お試しください。")
                return redirect('product:cart_detail')
            except OperationalError:
                messages.error(request, "一時的な問題が発生しました。時間をおいて再度お試しください。")
                return redirect('product:cart_detail')

            if send_order_confirmation_email(order):
                messages.success(request, "ご購入ありがとうございます。確認メールを送信しました。")
            else:
                messages.warning(request, "ご購入は完了しましたが、確認メールの送信に失敗しました。")
            return redirect('product:product_list')
        
        messages.error(request, "入力内容に不備があります。各項目のエラーを確認してください。")
        return render(request, 'product/cart.html', build_cart_page_context(request, cart, form=form))
    return redirect('product:cart_detail')


def apply_coupon(request):
    if request.method == 'POST':
        code_str = request.POST.get('promo_code', '').strip()

        if request.session.get('applied_promo') == code_str:
            messages.info(request, "そのコードはすでに適用されています。")
            return redirect('product:cart_detail')

        promo = fetch_unused_promotion(code_str)
        if promo is None:
            messages.error(request, "無効なコード、または既に使用されています。")
            request.session.pop('applied_promo', None)
        else:
            request.session['applied_promo'] = code_str
            messages.success(request, f"クーポン「{code_str}」を適用しました。")

    return redirect('product:cart_detail')
