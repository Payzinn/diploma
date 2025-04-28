from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Portfolio, Order, SphereType, Response, Message
from django.core.exceptions import ValidationError

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



class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = [
            'sphere_type',
            'less_than_year',
            'years_experience',
            'hourly_rate',
            'monthly_rate',
            'description',
        ]
        widgets = {
            'sphere_type': forms.HiddenInput(),

            'years_experience': forms.NumberInput(attrs={
                'class': 'portfolio-form__input',
                'type': 'number',
                'min': '0',
                'placeholder': '0',
            }),

            'hourly_rate': forms.NumberInput(attrs={
                'class': 'portfolio-form__input',
                'type': 'number',
                'min': '0',
                'placeholder': '₽/час',
            }),

            'monthly_rate': forms.NumberInput(attrs={
                'class': 'portfolio-form__input',
                'type': 'number',
                'min': '0',
                'placeholder': '₽/мес',
            }),

            'description': forms.Textarea(attrs={
                'class': 'portfolio-form__textarea',
                'placeholder': 'Кратко о ваших ключевых проектах',
                'rows': 5,
            }),
        }

    def clean(self):
        cleaned = super().clean()
        lt    = cleaned.get('less_than_year')
        years = cleaned.get('years_experience')

        if lt:
            cleaned['years_experience'] = None
        else:
            if years is None:
                self.add_error(
                    'years_experience',
                    'Укажите опыт работы или выберите «меньше года»'
                )
        return cleaned
    

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'title',
            'description',
            'sphere_type',
            'price',
            'is_negotiable',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название заказа',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Описание заказа',
                'rows': 6,
                'required': True,
            }),
            'sphere_type': forms.HiddenInput(attrs={
                'id': 'chosen_sphere',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Бюджет в руб.',
                'min': 0,
            }),
            'is_negotiable': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }
        labels = {
            'is_negotiable': 'Договорная цена (жду предложений)',
        }

    def clean(self):
        cleaned = super().clean()
        title         = cleaned.get('title')
        description   = cleaned.get('description')
        st            = cleaned.get('sphere_type')
        price         = cleaned.get('price')
        is_negotiable = cleaned.get('is_negotiable')

        if not title:
            self.add_error('title', 'Введите название заказа')
        if not description:
            self.add_error('description', 'Введите описание заказа')
        if not st:
            self.add_error('sphere_type', 'Выберите сферу деятельности')

        if is_negotiable:
            if price not in (None, ''):
                self.add_error('price',
                    'При договорной цене поле «Цена» должно быть пустым')
        else:
            if price in (None, ''):
                self.add_error('price',
                    'Укажите цену или выберите «Договорная цена»')

        return cleaned
    
class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['description', 'term', 'responser_price']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Расскажите, почему именно вы подойдёте для этого заказа',
                'rows': 4,
                'required': True,
            }),
            'term': forms.NumberInput(attrs={
                'class': 'form-input form-input--small',
                'placeholder': 'Срок в днях',
                'min': 1,
                'required': True,
            }),
            'responser_price': forms.NumberInput(attrs={
                'class': 'form-input form-input--small',
                'placeholder': 'Ваша цена в ₽',
                'min': 0,
                'required': True,
            }),
        }
        labels = {
            'responser_price': 'Ваша цена (₽)',
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Введите сообщение...'
            }),
        }
        labels = {'text': ''}