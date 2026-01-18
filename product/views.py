import base64
from typing import Tuple, Optional

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db.models import F

from .models import Product, Cart, CartItem


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
        return cart, True  # 取得できなかった

    # 正常取得できた場合
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

        return render(request, 'product/cart.html', {
            'cart_items': cart_items, 
            'total_price': total_price, 
            'cart_count': cart_count
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
        
        # 4. メッセージを表示
        messages.success(request, mark_safe(f'{product.name}をカートに追加しました。'))

        # 5. リダイレクト（ここは以前のまま）
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


