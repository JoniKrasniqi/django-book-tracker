from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count
from django.contrib import messages
from .models import Book
from .forms import RegistrationForm, BookForm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import re
import os
import threading
import json

# Global variable to store scraping progress
scraping_progress = {}

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def home(request):
    query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')  # Default sorting by newest first
    
    if sort_by not in ['title', '-title', 'price', '-price', 'stock', '-stock', 'reviews', '-reviews', 'created_at', '-created_at']:
        sort_by = '-created_at'  # Default if invalid sort parameter
    
    if query:
        books = Book.objects.filter(
            Q(title__icontains=query) & Q(created_by=request.user)
        ).order_by(sort_by)
    else:
        books = Book.objects.filter(created_by=request.user).order_by(sort_by)
    
    # Admin can see all books
    if request.user.is_superuser:
        if query:
            books = Book.objects.filter(title__icontains=query).order_by(sort_by)
        else:
            books = Book.objects.all().order_by(sort_by)
    
    # Statistics
    total_books = books.count()
    scraped_books = books.filter(source='SCRAPED').count()
    manual_books = books.filter(source='MANUAL').count()
    
    # For admin only - top contributors
    top_contributors = None
    if request.user.is_superuser:
        top_contributors = Book.objects.values('created_by__username').annotate(
            book_count=Count('id')
        ).order_by('-book_count')[:5]
    
    # Pagination
    paginator = Paginator(books, 5)  # 5 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'total_books': total_books,
        'scraped_books': scraped_books,
        'manual_books': manual_books,
        'top_contributors': top_contributors,
    }
    
    # For AJAX search requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        book_list = []
        for book in page_obj:
            book_list.append({
                'id': book.id,
                'title': book.title,
                'price': str(book.price),
                'stock': book.stock,
                'upc': book.upc,
                'reviews': book.reviews,
                'created_by': book.created_by.username,
                'created_at': book.created_at.strftime('%Y-%m-%d %H:%M'),
                'source': book.source,
            })
        return JsonResponse({
            'books': book_list,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_number': page_obj.number,
            'total_pages': paginator.num_pages,
        })
    
    return render(request, 'books/home.html', context)

@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.created_by = request.user
            book.source = 'MANUAL'
            book.save()
            return redirect('home')
    else:
        form = BookForm()
    return render(request, 'books/book_form.html', {'form': form})

@login_required
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # Check if user has permission to edit this book
    if not request.user.is_superuser and book.created_by != request.user:
        return HttpResponseForbidden("You don't have permission to edit this book")
    
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_form.html', {'form': form})

@login_required
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # Check if user has permission to delete this book
    if not request.user.is_superuser and book.created_by != request.user:
        return HttpResponseForbidden("You don't have permission to delete this book")
    
    if request.method == 'POST':
        book.delete()
        return redirect('home')
    
    return render(request, 'books/confirm_delete.html', {'book': book})

@login_required
def scrape_books(request):
    # Check if this is an AJAX request to start scraping
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
        # Generate a unique identifier for this scraping session
        import uuid
        session_id = str(uuid.uuid4())
        
        # Initialize progress tracking for this session
        scraping_progress[session_id] = {
            'completed_pages': 0,
            'total_pages': 0,
            'books_scraped': 0,
            'errors': [],
            'status': 'initializing',
            'finished': False
        }
        
        # Start scraping in a background thread
        thread = threading.Thread(
            target=perform_scraping,
            args=(request.user, session_id)
        )
        thread.daemon = True
        thread.start()
        
        # Return the session ID to the client
        return JsonResponse({
            'session_id': session_id,
            'message': 'Scraping started'
        })
    
    # If it's a regular GET request, render the scrape form page
    # Get assigned pages for this user to display in the template
    assigned_pages = get_user_pages(request.user.username)
    
    return render(request, 'books/scrape_form.html', {
        'assigned_pages': assigned_pages
    })

@login_required
def check_scrape_progress(request, session_id):
    """AJAX endpoint to check scraping progress"""
    if session_id in scraping_progress:
        progress = scraping_progress[session_id]
        
        # If scraping finished and this is the first time checking after completion,
        # keep it for this request but mark for cleanup
        if progress['finished'] and 'cleanup_marker' not in progress:
            progress['cleanup_marker'] = True
            
        # Clean up completed sessions after returning results
        if 'cleanup_marker' in progress:
            # Schedule cleanup after response is sent
            import threading
            def delayed_cleanup():
                import time
                time.sleep(10)  # Keep data for 10 more seconds
                if session_id in scraping_progress:
                    del scraping_progress[session_id]
            cleanup_thread = threading.Thread(target=delayed_cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
        return JsonResponse(progress)
    else:
        return JsonResponse({
            'error': 'Session not found',
            'finished': True
        }, status=404)

def perform_scraping(user, session_id):
    """Background task to perform the actual scraping"""
    # Get user's assigned pages
    user_pages = get_user_pages(user.username)
    
    if not user_pages and not user.is_superuser:
        scraping_progress[session_id].update({
            'status': 'error',
            'errors': ['You do not have any assigned pages to scrape.'],
            'finished': True
        })
        return
    
    # Admin can scrape pages 1-6
    if user.is_superuser:
        user_pages = list(range(1, 7))  # Pages 1-6
    
    scraping_progress[session_id]['total_pages'] = len(user_pages)
    scraping_progress[session_id]['status'] = 'scraping'
    
    # Setup Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    scraped_books = []
    errors = []
    
    try:
        # Initialize WebDriver using the chromedriver.exe in the downloaded folder
        chrome_install = ChromeDriverManager().install()
        folder = os.path.dirname(chrome_install)
        chromedriver_path = os.path.join(folder, "chromedriver.exe")
        
        service = ChromeService(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Track scraping progress
        for page_num in user_pages:
            try:
                scraping_progress[session_id]['current_page'] = page_num
                
                url = f"https://books.toscrape.com/catalogue/page-{page_num}.html"
                driver.get(url)
                
                # Extract book links from the page
                book_links = []
                book_elements = driver.find_elements(By.CSS_SELECTOR, "article.product_pod h3 a")
                
                for element in book_elements:
                    href = element.get_attribute("href")
                    if href:
                        book_links.append(href)
                
                # Visit each book page and extract detailed information
                for book_url in book_links:
                    try:
                        driver.get(book_url)
                        
                        # Extract book data
                        title = driver.find_element(By.CSS_SELECTOR, ".product_main h1").text
                        
                        # Extract price (remove currency symbol)
                        price_text = driver.find_element(By.CSS_SELECTOR, ".price_color").text
                        price = float(re.sub(r'[^\d.]', '', price_text))
                        
                        # Extract stock information
                        stock_text = driver.find_element(By.CSS_SELECTOR, ".instock.availability").text.strip()
                        stock_match = re.search(r'(\d+)', stock_text)
                        stock = int(stock_match.group(1)) if stock_match else 0
                        
                        # Extract product description
                        try:
                            description = driver.find_element(By.CSS_SELECTOR, "#product_description + p").text
                        except NoSuchElementException:
                            description = "No description available"
                        
                        # Extract UPC and review count from product information table
                        table_rows = driver.find_elements(By.CSS_SELECTOR, "table.table-striped tr")
                        upc = ""
                        reviews = 0
                        
                        for row in table_rows:
                            header = row.find_element(By.CSS_SELECTOR, "th").text
                            value = row.find_element(By.CSS_SELECTOR, "td").text
                            
                            if header == "UPC":
                                upc = value
                            elif header == "Number of reviews":
                                reviews = int(value)
                        
                        # Create or update book in database
                        book, created = Book.objects.update_or_create(
                            title=title,
                            created_by=user,
                            defaults={
                                'price': price,
                                'stock': stock,
                                'description': description,
                                'upc': upc,
                                'reviews': reviews,
                                'source': 'SCRAPED'
                            }
                        )
                        
                        scraped_books.append(book)
                        scraping_progress[session_id]['books_scraped'] += 1
                    
                    except Exception as e:
                        error_msg = f"Error scraping book {book_url}: {str(e)}"
                        errors.append(error_msg)
                        if session_id in scraping_progress:
                            scraping_progress[session_id]['errors'].append(error_msg)
                
                scraping_progress[session_id]['completed_pages'] += 1
                
            except Exception as e:
                error_msg = f"Error scraping page {page_num}: {str(e)}"
                errors.append(error_msg)
                if session_id in scraping_progress:
                    scraping_progress[session_id]['errors'].append(error_msg)
    
    except Exception as e:
        error_msg = f"Error during scraping: {str(e)}"
        errors.append(error_msg)
        if session_id in scraping_progress:
            scraping_progress[session_id]['errors'].append(error_msg)
    
    finally:
        # Close the browser if it was initialized
        if driver:
            driver.quit()
        
        if session_id in scraping_progress:
            scraping_progress[session_id].update({
                'status': 'completed',
                'success': len(scraped_books) > 0,
                'books_count': len(scraped_books),
                'finished': True
            })
    
    return

def get_user_pages(username):
    """Return the page numbers assigned to a specific user"""
    user_page_mapping = {
        'name_of_user_1': [1, 2],
        'name_of_user_2': [3, 4],
        'name_of_user_3': [5, 6],
    }
    return user_page_mapping.get(username, [])
