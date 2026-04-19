# Generated migration - creates permanent default users

from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_users(apps, schema_editor):
    """Create default superadmin, admin, and testuser accounts."""
    User = apps.get_model('authentication', 'User')
    from django.contrib.auth.hashers import make_password
    
    # Create or update superadmin
    superadmin, created = User.objects.get_or_create(
        username='superadmin',
        defaults={
            'email': 'superadmin@certeye.local',
            'password': make_password('Admin@123456'),
            'role': 'superadmin',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        print(f"✓ Created superadmin user")
    else:
        print(f"⊘ Superadmin already exists")
    
    # Create or update admin
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@certeye.local',
            'password': make_password('Admin@123456'),
            'role': 'admin',
            'is_active': True,
            'is_staff': True,
            'is_superuser': False,
        }
    )
    if created:
        print(f"✓ Created admin user")
    else:
        print(f"⊘ Admin already exists")
    
    # Create or update testuser
    testuser, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'testuser@certeye.local',
            'password': make_password('Test@123456'),
            'role': 'user',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
        }
    )
    if created:
        print(f"✓ Created testuser user")
    else:
        print(f"⊘ Testuser already exists")


def reverse_default_users(apps, schema_editor):
    """Reverse function - removes created users (careful with production)."""
    User = apps.get_model('authentication', 'User')
    usernames = ['superadmin', 'admin', 'testuser']
    
    for username in usernames:
        try:
            user = User.objects.get(username=username)
            user.delete()
            print(f"✓ Deleted user: {username}")
        except User.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_userauditlog_userloginlog_userregistrationlog'),
    ]

    operations = [
        migrations.RunPython(create_default_users, reverse_default_users),
    ]
