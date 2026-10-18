import re

from django import forms
from django.utils import timezone

from .models import Order


def passes_luhn_check(card_number):
    """カード番号の各桁からチェックサムを計算する。"""
    # カード番号を右端から読む
    # 右から2番目、4番目、6番目……の数字を2倍する
    # 2倍した結果が10以上なら9を引く
    # 全数字の合計が10で割り切れば合格
    total = 0

    for index, character in enumerate(reversed(card_number)):
        digit = int(character)

        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9

        total += digit

    return total % 10 == 0


class OrderForm(forms.ModelForm):
    # カード情報は疑似決済の入力検証にだけ使用し、Orderモデルには保存しない。
    card_name = forms.CharField(
        label='カード名義',
        max_length=100,
        error_messages={'required': 'カード名義を入力してください。'},
    )
    card_number = forms.CharField(
        label='カード番号',
        max_length=16,
        error_messages={'required': 'カード番号を入力してください。'},
    )
    card_expiry = forms.CharField(
        label='有効期限',
        max_length=5,
        error_messages={'required': '有効期限を入力してください。'},
    )

    class Meta:
        model = Order
        fields = [
            'last_name',
            'first_name',
            'username',
            'email',
            'address',
            'card_name',
            'card_number',
            'card_expiry',
        ]

        error_messages = {
            'last_name': {'required': '姓を入力してください。'},
            'first_name': {'required': '名を入力してください。'},
            'username': {'required': 'ユーザー名を入力してください。'},
            'email': {
                'required': 'メールアドレスを入力してください。',
                'invalid': '有効なメールアドレスを入力してください。',
            },
            'address': {'required': '住所を入力してください。'},
        }
        
        widgets = {
            'last_name': forms.TextInput(attrs={'placeholder': '姓', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': '名', 'class': 'form-control'}),
            'username': forms.TextInput(attrs={'placeholder': 'ユーザー名', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'メールアドレス', 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'placeholder': '住所', 'class': 'form-control'}),
        }

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number']

        if not card_number.isdigit():
            raise forms.ValidationError('カード番号は数字のみで入力してください。')

        if len(card_number) != 16:
            raise forms.ValidationError('カード番号は16桁で入力してください。')

        if not passes_luhn_check(card_number):
            raise forms.ValidationError('カード番号の形式が正しくありません。')

        return card_number

    def clean_card_expiry(self):
        expiry = self.cleaned_data['card_expiry'].strip()
        match = re.fullmatch(r'(\d{2})/(\d{2})', expiry)

        if match is None:
            raise forms.ValidationError('有効期限は MM/YY の形式で入力してください。')

        month = int(match.group(1))
        year = 2000 + int(match.group(2))

        if not 1 <= month <= 12:
            raise forms.ValidationError('有効期限の月は01〜12で入力してください。')

        today = timezone.localdate()
        if (year, month) < (today.year, today.month):
            raise forms.ValidationError('有効期限が切れています。')

        return expiry
