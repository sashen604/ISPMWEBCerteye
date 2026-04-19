from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superadmin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='superadmin',
            help='Superadmin username'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='superadmin@certeye.local',
            help='Superadmin email'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='SuperAdmin123!',
            help='Superadmin password'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Check if superadmin already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superadmin user "{username}" already exists')
            )
            return

        # Create superadmin
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=User.ROLE_SUPERADMIN,
            is_staff=True,
            is_superuser=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Superadmin user created successfully!\n'
                f'   Username: {username}\n'
                f'   Email: {email}\n'
                f'   Password: {password}\n'
                f'   Role: Super Admin'
            )
        )
