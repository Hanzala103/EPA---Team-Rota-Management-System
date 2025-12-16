from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Team


# -------------------------------
# LOGIN FORM (just fields + basic validation)
# -------------------------------
class LoginForm(forms.Form):
    identifier = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email or username',
            'autofocus': True
        }),
        label="Email or Username"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        }),
        label="Password"
    )

    def clean_identifier(self):
        identifier = self.cleaned_data['identifier']
        return identifier.strip()

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get('identifier')
        password = cleaned_data.get('password')
        if identifier and password:
            user = authenticate(username=identifier, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username/email or password.")
            if not user.is_active:
                raise forms.ValidationError("This account is inactive.")
            self.user = user
        return cleaned_data


# -------------------------------
# REGISTER FORM (unchanged original)
# -------------------------------
class RegisterForm(UserCreationForm):
    team = forms.ModelChoiceField(queryset=Team.objects.all(), required=False)

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'department',
            'phone',
            'default_start_time',
            'default_end_time',
            'timezone',
            'team',
            'password1',
            'password2',
            'role',
        ]
