from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from .forms import OrderForm, passes_luhn_check
from .models import Order


class OrderFormCardValidationTests(SimpleTestCase):
    def valid_form_data(self, **overrides):
        data = {
            'last_name': '山田',
            'first_name': '太郎',
            'username': 'taro',
            'email': 'taro@example.com',
            'address': '東京都',
            'card_name': 'TARO YAMADA',
            'card_number': '4242424242424242',
            'card_expiry': '12/28',
        }
        data.update(overrides)
        return data

    @patch('product.forms.timezone.localdate', return_value=date(2026, 10, 3))
    def test_valid_card_information_passes_validation(self, _mock_localdate):
        form = OrderForm(self.valid_form_data())

        self.assertTrue(form.is_valid(), form.errors)

    @patch('product.forms.timezone.localdate', return_value=date(2026, 10, 3))
    def test_current_month_is_not_expired(self, _mock_localdate):
        form = OrderForm(self.valid_form_data(card_expiry='10/26'))

        self.assertTrue(form.is_valid(), form.errors)

    def test_expiry_month_must_be_between_01_and_12(self):
        for expiry in ('00/28', '13/28'):
            with self.subTest(expiry=expiry):
                form = OrderForm(self.valid_form_data(card_expiry=expiry))

                self.assertFalse(form.is_valid())
                self.assertIn(
                    '有効期限の月は01〜12で入力してください。',
                    form.errors['card_expiry'],
                )

    @patch('product.forms.timezone.localdate', return_value=date(2026, 10, 3))
    def test_past_expiry_is_rejected(self, _mock_localdate):
        form = OrderForm(self.valid_form_data(card_expiry='09/26'))

        self.assertFalse(form.is_valid())
        self.assertIn('有効期限が切れています。', form.errors['card_expiry'])

    def test_card_number_must_pass_luhn_check(self):
        form = OrderForm(
            self.valid_form_data(card_number='4242424242424241')
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            'カード番号の形式が正しくありません。',
            form.errors['card_number'],
        )

    def test_luhn_check_with_known_numbers(self):
        self.assertTrue(passes_luhn_check('4242424242424242'))
        self.assertFalse(passes_luhn_check('4242424242424241'))

    def test_card_fields_are_not_part_of_order_model(self):
        model_field_names = {field.name for field in Order._meta.fields}

        self.assertTrue(
            {'card_name', 'card_number', 'card_expiry'}.isdisjoint(
                model_field_names
            )
        )
