import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_service.settings')
django.setup()

from accounts.models import User

users = []
roles = {
    'Admin': {'is_superuser': True, 'is_staff': True},
    'Support': {'is_staff': True, 'is_superuser': False},
    'Supplier': {'is_supplier': True},
    'Delivery': {'is_delivery': True}
}

for role_name, kwargs in roles.items():
    u = User.objects.filter(**kwargs).first()
    
    if u:
        u.set_password('Test@1234')
        u.save()
        users.append(f'{role_name}: {u.email} / Test@1234')
    else:
        email = f'{role_name.lower()}@test.com'
        u = User.objects.create(
            email=email, 
            first_name=role_name, 
            last_name='User',
            **kwargs
        )
        u.set_password('Test@1234')
        u.save()
        users.append(f'{role_name}: {u.email} / Test@1234')

print('\n=== TEST ACCOUNTS ===')
for line in users:
    print(line)
print('=====================')
