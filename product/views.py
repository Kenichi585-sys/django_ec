import base64
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Product
from django.views import View
from django.shortcuts import redirect
from django.contrib import messages

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
    

class CartView(ListView):
    model = Product
    template_name = 'product/cart.html'

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            cart_ids = self.request.session.get('cart', {})
            cart_products =  Product.objects.filter(pk__in=cart_ids)
            
            cart_items = []
            for p in cart_products:
                quantity = cart_ids[ str(p.pk) ]
                subtotal = p.price * quantity
                item = {
                    'product': p,
                    'quantity': quantity,
                    'subtotal': subtotal,
                }
                cart_items.append(item)

            context['cart_items'] = cart_items

            context['total_price'] = sum([item['subtotal'] for item in cart_items])

            return context
    

class CartAddView(View):
    def post(self, request, pk):
        cart = request.session.get('cart', {})
        pk = str(pk)
        product = Product.objects.get(pk=pk)

        quantity = int(request.POST.get('quantity', 1))

        if pk in cart:
            cart[pk] += quantity
        else:
            cart[pk] = quantity
            
        messages.success(request, f'{product.name}をカートに追加しました。{product.name}は現在カートに{cart[pk]}個入っています。')

        request.session['cart'] = cart

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
        cart = request.session.get('cart', {})
        pk = str(pk)

        if pk in cart:
            cart.pop(pk, None)

        request.session['cart'] = cart
        return redirect('product:cart_detail')


class CartDecreaseView(View):
    def post(self, request, pk):
        cart = request.session.get('cart', {})
        pk = str(pk)

        if pk in cart:
            if cart[pk] > 1:
                cart[pk] -= 1
            else:
                cart.pop(pk, None)

        request.session['cart'] = cart

        return redirect('product:cart_detail')