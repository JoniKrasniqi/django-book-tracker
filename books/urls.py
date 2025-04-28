from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('add/', views.add_book, name='add_book'),
    path('edit/<int:pk>/', views.edit_book, name='edit_book'),
    path('delete/<int:pk>/', views.delete_book, name='delete_book'),
    path('scrape-progress/<str:session_id>/', views.check_scrape_progress, name='check_scrape_progress'),
    path('scrape/', views.scrape_books, name='scrape_books'),
] 