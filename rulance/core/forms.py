from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(label="ФИО", max_length=100)
    email = forms.EmailField(label="Email")
    role = forms.ChoiceField(label="Роль", choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['full_name', 'username', 'email', 'password1', 'password2', 'role']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Эта почта уже используется")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Этот логин уже занят")
        return username

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'avatar']

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Максимальный размер файла 2 МБ")
        return avatar
    
class AvatarForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['avatar']