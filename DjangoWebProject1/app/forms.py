"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Review, Order, Post, Comment

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses bootstrap CSS."""
    username = forms.CharField(max_length=254,
                                widget=forms.TextInput({
                                'class': 'form-control',
                                'placeholder': 'Имя пользователя'}))
    password = forms.CharField(label=_("Пароль"),
                                widget=forms.PasswordInput({
                                    'class': 'form-control',
                                    'placeholder': 'Пароль'}))

class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    update = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        label='Рейтинг',
        choices=[(1, '1 - Ужасно'), (2, '2 - Плохо'), (3, '3 - Средне'), (4, '4 - Хорошо'), (5, '5 - Отлично')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Review
        fields = ('rating', 'text')
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'text': 'Текст отзыва',
        }


class OrderCreateForm(forms.ModelForm):
    delivery_service = forms.ChoiceField(
        choices=Order.DELIVERY_CHOICES,
        widget=forms.RadioSelect,
        initial='cdek',
        label='Служба доставки'
    )
    cdek_point = forms.CharField(label='Пункт выдачи СДЭК', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    post_office_address = forms.CharField(label='Адрес почтового отделения', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city', 'delivery_service', 'cdek_point', 'post_office_address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'image', 'slug')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Заголовок',
            'text': 'Текст поста',
            'image': 'Изображение',
            'slug': 'Слаг',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Напишите комментарий...'}),
        }
        labels = {
            'text': '',
        }
