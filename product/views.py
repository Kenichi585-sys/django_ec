import base64
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Product, Cart, CartItem
from django.views import View
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.safestring import mark_safe


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
        cart_id = request.session.get('cart_id')
        total_price = 0
        cart_count = 0

        if cart_id:
            try:
                cart = Cart.objects.get(pk=cart_id)
                cart_items = CartItem.objects.filter(cart=cart).select_related('product')

            except Cart.DoesNotExist:
                cart_items = []
                messages.warning(request, "長期間操作がなかったため、カートの情報が更新されました。")
        else:
            cart_items = []
        
        return render(request, 'product/cart.html', {'cart_items': cart_items, 'total_price': total_price, 'cart_count': cart_count})
    
    
class CartAddView(View):
    def post(self, request, pk):
        pk = str(pk)
        product = Product.objects.get(pk=pk)
        quantity = int(request.POST.get('quantity', 1))

        cart_id = request.session.get('cart_id')

        if cart_id:
            try:
                cart = Cart.objects.get(pk=cart_id)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.pk
        
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.pk

        existing_item = CartItem.objects.filter(cart=cart, product=product).first()
                
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
        else:
            existing_item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)
            
        messages.success(request, mark_safe(f'{product.name}をカートに追加しました。<br>カートの中の{product.name}の数量：{existing_item.quantity}点'))

        next_page = request.POST.get('next')
        if next_page == 'product_detail':
            return redirect('product:product_detail', pk=pk)
        elif next_page:
            return redirect('product:' + next_page)
        
        return redirect('product:product_list')


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


class CartDeleteView(View):
    def post(self, request, pk):
        cart_id = request.session.get('cart_id')
        if not cart_id:
            return redirect('product:cart_detail')

        try:
            cart = Cart.objects.get(pk=cart_id)
        except Cart.DoesNotExist:
            return redirect('product:cart_detail')

        pk = str(pk)
        product = Product.objects.get(pk=pk)
        CartItem.objects.filter(cart=cart, product=pk).delete()
        messages.info(request, f'{product.name}をカートから削除しました')
        return redirect('product:cart_detail')


class CartDecreaseView(View):
    def post(self, request, pk):
        cart_id = request.session.get('cart_id')
        if not cart_id:
            return redirect('product:cart_detail')

        try:
            cart = Cart.objects.get(pk=cart_id)
            pk = str(pk)
            cart_item = CartItem.objects.filter(cart=cart, product=pk).first()
        except Cart.DoesNotExist:
            return redirect('product:cart_detail')
        
        if not cart_item:
            return redirect('product:cart_detail')
        
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()

        return redirect('product:cart_detail')

