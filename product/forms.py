from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['last_name', 'first_name', 'username', 'email', 'address']
        
        widgets = {
            'last_name': forms.TextInput(attrs={'placeholder': '姓', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': '名', 'class': 'form-control'}),
            'username': forms.TextInput(attrs={'placeholder': 'ユーザー名', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'メールアドレス', 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'placeholder': '住所', 'class': 'form-control'}),
        }
