import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seguros.settings')

import django
django.setup()

from accounts.models import UserProfile

for u in UserProfile.objects.all():
    u.set_password('Seguros2025!')
    u.save()
    print(f'Updated password for {u.username}')