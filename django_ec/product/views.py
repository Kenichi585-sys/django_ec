from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Product


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