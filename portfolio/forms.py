from django import forms
from django.contrib.auth.models import User
from .models import Transaction, PriceAlert, CURRENCY_CHOICES

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError('Passwords do not match')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['asset', 'tx_type', 'quantity', 'price_per_unit', 'fee', 'currency', 'timestamp']
        widgets = {
            'timestamp': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CurrencySelectorForm(forms.Form):
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, initial='INR')


class PriceAlertForm(forms.ModelForm):
    class Meta:
        model = PriceAlert
        fields = ['asset', 'target_price', 'currency', 'is_above']
