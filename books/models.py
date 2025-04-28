from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(verbose_name="Quantity in stock")
    description = models.TextField()
    upc = models.CharField(max_length=50)
    reviews = models.IntegerField(verbose_name="Number of reviews")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    source = models.CharField(max_length=20, choices=[
        ('SCRAPED', 'Scraped from website'),
        ('MANUAL', 'Added manually')
    ], default='MANUAL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
