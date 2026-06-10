from django.contrib.auth import get_user_model

User = get_user_model()

username = "admin"
password = "iceman"

if not User.objects.filter(username=username).exists():
    User.objects.create_user(username=username, password=password)
    print("Admin user created.")
else:
    print("Admin user already exists.")