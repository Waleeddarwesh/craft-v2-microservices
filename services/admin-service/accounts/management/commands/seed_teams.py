from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import User

class Command(BaseCommand):
    help = 'Create demo accounts for the 4 specific dashboard teams (Admin, Operations, Sales, Support)'

    def handle(self, *args, **options):
        teams = [
            {'email': 'admin@craft.com', 'first_name': 'Admin', 'last_name': 'User', 'group': 'Admin', 'is_superuser': True},
            {'email': 'operations@craft.com', 'first_name': 'Operations', 'last_name': 'User', 'group': 'Operations', 'is_superuser': False},
            {'email': 'sales@craft.com', 'first_name': 'Sales', 'last_name': 'User', 'group': 'Sales', 'is_superuser': False},
            {'email': 'support@craft.com', 'first_name': 'Support', 'last_name': 'User', 'group': 'Support', 'is_superuser': False},
        ]

        for team in teams:
            user, created = User.objects.get_or_create(
                email=team['email'],
                defaults={
                    'first_name': team['first_name'],
                    'last_name': team['last_name'],
                    'is_staff': True,
                    'is_superuser': team['is_superuser'],
                    'is_verified': True
                }
            )
            
            if created:
                user.set_password('craftpassword123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user {team['email']}"))
            else:
                self.stdout.write(self.style.WARNING(f"User {team['email']} already exists"))
                
            try:
                group = Group.objects.get(name=team['group'])
                user.groups.add(group)
                self.stdout.write(self.style.SUCCESS(f"Assigned {team['email']} to group {team['group']}"))
            except Group.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Group {team['group']} does not exist! Run setup_roles first."))

        self.stdout.write(self.style.SUCCESS('Successfully seeded 4 custom dashboard team accounts!'))
