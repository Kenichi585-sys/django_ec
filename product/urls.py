from django.contrib import admin
from django.urls import path
from .views import (ProductListView, ProductDetailView, ProductCreateView, 
                    ProductUpdateView, ProductDeleteView, ProductManageListView, 
                    CartView, CartAddView, CartDeleteView)


app_name = 'product'
urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('manage/products/', ProductManageListView.as_view(), name='manage_list'),
    path('manage/products/create/', ProductCreateView.as_view(), name='product_create'),
    path('manage/products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('manage/products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('cart/', CartView.as_view(), name='cart_detail'),
    path('cart/add/<int:pk>/', CartAddView.as_view(), name='add_to_cart'),
    path('cart/delete/<int:pk>/', CartDeleteView.as_view(), name='delete_from_cart'),
]
