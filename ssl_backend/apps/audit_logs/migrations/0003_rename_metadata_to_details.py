# Migration to rename metadata to details for consistency

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit_logs', '0002_enhanced_audit_logs'),
    ]

    operations = [
        migrations.RenameField(
            model_name='auditlog',
            old_name='metadata',
            new_name='details',
        ),
    ]
