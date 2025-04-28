import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def create_users():
    # Define the users to create
    users = [
        {'username': 'name_of_user_1', 'password': 'BookTracker123!', 'is_staff': False, 'is_superuser': False},
        {'username': 'name_of_user_2', 'password': 'BookTracker123!', 'is_staff': False, 'is_superuser': False},
        {'username': 'name_of_user_3', 'password': 'BookTracker123!', 'is_staff': False, 'is_superuser': False},
        {'username': 'name_of_admin', 'password': 'AdminTracker123!', 'is_staff': True, 'is_superuser': True},
    ]
    
    # Create each user
    for user_data in users:
        username = user_data['username']
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"User '{username}' already exists. Skipping...")
            continue
        
        # Create the user
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=user_data['password']
        )
        
        # Set staff and superuser status
        user.is_staff = user_data['is_staff']
        user.is_superuser = user_data['is_superuser']
        user.save()
        
        print(f"Created user: {username}")

if __name__ == "__main__":
    print("Creating required users...")
    create_users()
    print("User creation completed.") 