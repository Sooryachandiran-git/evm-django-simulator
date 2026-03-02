import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evm_project.settings')
django.setup()

from django.contrib.auth.models import User

# Check if user exists
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser created successfully: username='admin', password='admin'")
else:
    # If it exists, let's just force the password to 'admin' so you can definitely log in
    u = User.objects.get(username='admin')
    u.set_password('admin')
    u.save()
    print("Password for existing 'admin' user was reset to 'admin'")
