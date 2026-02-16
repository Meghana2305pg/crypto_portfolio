from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Transaction, PriceAlert, CURRENCY_CHOICES


# ==============================
# 🔐 REGISTER FORM
# ==============================

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"})
    )

    class Meta:
        model = User
        fields = ["username", "email"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Enter username"}),
            "email": forms.EmailInput(attrs={"placeholder": "Enter email"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords do not match.")

            # Django password strength validation
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error("password", e)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# ==============================
# 💰 TRANSACTION FORM
# ==============================

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            "asset",
            "tx_type",
            "quantity",
            "price_per_unit",
            "fee",
            "currency",
            "timestamp",
        ]
        widgets = {
            "timestamp": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


# ==============================
# 💱 CURRENCY SELECTOR
# ==============================

class CurrencySelectorForm(forms.Form):
    currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        initial="INR",
    )


# ==============================
# 🚨 PRICE ALERT FORM
# ==============================

class PriceAlertForm(forms.ModelForm):
    class Meta:
        model = PriceAlert
        fields = ["asset", "target_price", "currency", "is_above"]
