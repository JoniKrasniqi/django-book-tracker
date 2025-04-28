# Django Book Tracker System

A Django-based web application that allows authenticated users to scrape book data from an external source, store it in a database, and manage the data through a user-friendly interface.

## Features

- User authentication (register, login, logout)
- Role-based access control
- Web scraping with Selenium
- Book management (add, edit, delete)
- Search functionality
- Dashboard with statistics
- Responsive UI with Bootstrap

## Project Structure

- `book_tracker/` - Main project directory
- `config/` - Django settings and configuration
- `books/` - Django app containing all main functionality
  - `models.py` - Database models
  - `views.py` - Application views and business logic
  - `forms.py` - Form definitions
  - `urls.py` - URL routing
  - `templates/` - HTML templates
- `create_users.py` - Script to create required users
- `manage.py` - Django management script
- `requirements.txt` - Project dependencies

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Google Chrome (for Selenium)
- ChromeDriver (matching your Chrome version)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd book_tracker
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create required users:
   ```
   python create_users.py
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

7. Access the application at `http://127.0.0.1:8000/`

## Database

The application uses SQLite as its default database. The database file (`db.sqlite3`) will be created automatically when you run the migrations.

## User Credentials

The system comes with the following pre-configured users:

| Username        | Password        | Scraping Scope | Permissions                           |
|-----------------|-----------------|----------------|---------------------------------------|
| name_of_user_1  | BookTracker123! | Pages 1 and 2  | View, add, edit, delete own books only |
| name_of_user_2  | BookTracker123! | Pages 3 and 4  | View, add, edit, delete own books only |
| name_of_user_3  | BookTracker123! | Pages 5 and 6  | View, add, edit, delete own books only |
| name_of_admin   | AdminTracker123!| All pages      | Full access to all users' data         |

## Bonus Features

- Dashboard with summary statistics:
  - Total books scraped
  - Number of books added manually 
  - Top contributors (visible to admin only)
- AJAX search functionality for a smoother user experience

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   - Ensure Chrome and ChromeDriver versions match
   - If using webdriver-manager, it will automatically handle version matching

2. **Database Migration Errors**
   - If you encounter migration errors, try:
     ```
     python manage.py migrate --fake
     python manage.py makemigrations
     python manage.py migrate
     ```

3. **Permission Issues**
   - Ensure the database file has proper read/write permissions
   - Check that the user running the application has necessary permissions

## Deployment Considerations

1. **Production Settings**
   - Update `DEBUG = False` in settings.py
   - Set proper `ALLOWED_HOSTS`
   - Configure a production database (PostgreSQL recommended)
   - Set up proper static file serving

2. **Security**
   - Change default user passwords
   - Set up proper HTTPS
   - Configure proper CORS settings if needed

## Notes on Implementation

- The web scraping functionality uses Selenium in headless mode
- Each user has a specific set of pages they can scrape from the target website
- The admin user has access to all books and can see additional statistics
- The UI is built with Bootstrap for a responsive design

## License

This project is licensed under the MIT License - see the LICENSE file for details. 