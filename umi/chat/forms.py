from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserSettings


class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'Username or Email',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'Password',
            'id': 'loginPassword',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input me-2',
            'id': 'rememberMe'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        if identifier and password:
            # Check if identifier is an email address
            user_obj = None
            if '@' in identifier:
                user_obj = User.objects.filter(email__iexact=identifier).first()
            if not user_obj:
                user_obj = User.objects.filter(username__iexact=identifier).first()

            if user_obj:
                authenticated_user = authenticate(username=user_obj.username, password=password)
                if authenticated_user:
                    cleaned_data['user'] = authenticated_user
                else:
                    raise forms.ValidationError("Invalid credentials. Please check your password.")
            else:
                raise forms.ValidationError("No account found matching the provided username or email.")

        return cleaned_data


class RegisterForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'Username (e.g. alex_dev)'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'Email Address (e.g. alex@example.com)'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'Last Name'
        })
    )
    password = forms.CharField(
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'Password (min 8 characters)',
            'id': 'regPassword'
        })
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'Confirm Password',
            'id': 'regConfirmPassword'
        })
    )
    profile_pic = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control form-control-sm rounded-pill',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data


class ForgotPasswordForm(forms.Form):
    email = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'Enter your registered Email Address or Username'
        })
    )


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'New Password (min 8 characters)',
            'id': 'resetNewPassword'
        })
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill px-3 py-2',
            'placeholder': 'Confirm New Password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control rounded-pill',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control rounded-pill',
        'placeholder': 'Last Name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control rounded-pill',
        'placeholder': 'Email'
    }))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control rounded-pill',
        'placeholder': 'Username'
    }))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = [
            'theme', 'profile_pic', 'ai_provider', 'ai_model', 'streaming', 'response_style'
        ]
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-select form-select-sm w-auto rounded-pill'}),
            'ai_provider': forms.Select(attrs={'class': 'form-select form-select-sm w-auto rounded-pill'}),
            'ai_model': forms.Select(attrs={'class': 'form-select form-select-sm w-auto rounded-pill'}),
            'streaming': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'response_style': forms.Select(attrs={'class': 'form-select form-select-sm w-auto rounded-pill'}),
        }
