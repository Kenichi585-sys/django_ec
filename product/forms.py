from django import forms
from .models import Order
import re

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['last_name', 'first_name', 'username', 'email', 'address',
                    'card_name', 'card_number', 'card_expiry']
        
        widgets = {
            'last_name': forms.TextInput(attrs={'placeholder': '姓', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': '名', 'class': 'form-control'}),
            'username': forms.TextInput(attrs={'placeholder': 'ユーザー名', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'メールアドレス', 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'placeholder': '住所', 'class': 'form-control'}),
        }

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        
        if not card_number.isdigit():
            raise forms.ValidationError("カード番号は数字のみで入力してください。")
        
        if len(card_number) != 16:
            raise forms.ValidationError("カード番号は16桁で入力してください。")
        return card_number

    def clean_card_expiry(self):
        expiry = self.cleaned_data.get('card_expiry')

        if not re.match(r'^\d{2}/\{2}$', expiry):
            raise forms.ValidationError("有効期限は MM/YY の形式で入力してください。")
        
        return expiry
