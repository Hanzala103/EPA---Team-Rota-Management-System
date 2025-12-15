from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


# -------------------------------
# LOGIN FORM (just fields + basic validation)
# -------------------------------
class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autofocus': True
        }),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        }),
        label="Password"
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        email = email.lower().strip()
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if email and password:
            try:
                user = CustomUser.objects.get(email=email)
                if user.check_password(password):
                    self.user = user
                else:
                    raise forms.ValidationError("Invalid email or password.")
            except CustomUser.DoesNotExist:
                raise forms.ValidationError("Invalid email or password.")
        return cleaned_data


# -------------------------------
# REGISTER FORM (unchanged original)
# -------------------------------
class RegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'department', 'phone', 'password1', 'password2', 'role']  # Added 'role'