from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Book
from django.core.validators import MinValueValidator

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

class BookForm(forms.ModelForm):
    title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title'}),
        help_text='Enter the complete book title'
    )
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        validators=[MinValueValidator(0, message="Price cannot be negative")],
        help_text='Enter the book price (in $)'
    )
    stock = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        validators=[MinValueValidator(0, message="Stock cannot be negative")],
        help_text='Enter the quantity available in stock'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter book description'}),
        help_text='Provide a detailed description of the book'
    )
    upc = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter UPC/ISBN'}),
        help_text='Enter the Universal Product Code or ISBN'
    )
    reviews = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        validators=[MinValueValidator(0, message="Number of reviews cannot be negative")],
        help_text='Enter the number of reviews'
    )
    
    class Meta:
        model = Book
        fields = ['title', 'price', 'stock', 'description', 'upc', 'reviews'] 