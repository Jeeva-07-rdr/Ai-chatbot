from django import forms
from django.contrib.auth.models import User
from .models import UserSettings

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
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


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
