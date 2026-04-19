# Generated migration - Enhanced audit logs with certificate and alert tracking

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('audit_logs', '0001_initial'),
    ]

    operations = [
        # Alter existing AuditLog model
        migrations.RemoveField(
            model_name='auditlog',
            name='actor',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='target',
        ),
        migrations.AddField(
            model_name='auditlog',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='target_type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='target_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('login', 'User Login'),
                    ('logout', 'User Logout'),
                    ('certificate_create', 'Certificate Created'),
                    ('certificate_update', 'Certificate Updated'),
                    ('certificate_delete', 'Certificate Deleted'),
                    ('certificate_scan', 'Certificate Scan'),
                    ('alert_create', 'Alert Created'),
                    ('alert_update', 'Alert Updated'),
                    ('alert_resolve', 'Alert Resolved'),
                    ('role_change', 'Role Changed'),
                    ('risk_config_update', 'Risk Configuration Updated'),
                    ('agent_submission', 'Agent Submission'),
                    ('internal_cert_submission', 'Internal Certificate Submission'),
                    ('other', 'Other Action'),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'created_at'], name='audit_logs__user_id_c_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', 'created_at'], name='audit_logs__action_c_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['target_type', 'target_id'], name='audit_logs__target__idx'),
        ),
        # Create CertificateAuditLog model
        migrations.CreateModel(
            name='CertificateAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('create', 'Created'),
                        ('update', 'Updated'),
                        ('delete', 'Deleted'),
                        ('scan', 'Scanned'),
                        ('import', 'Imported'),
                    ],
                    max_length=20,
                )),
                ('certificate_id', models.IntegerField(blank=True, null=True)),
                ('certificate_name', models.CharField(blank=True, max_length=255)),
                ('domain', models.CharField(blank=True, max_length=255)),
                ('old_values', models.JSONField(blank=True, default=dict)),
                ('new_values', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='certificateauditlog',
            index=models.Index(fields=['user', 'timestamp'], name='audit_logs__user_id_t_idx'),
        ),
        migrations.AddIndex(
            model_name='certificateauditlog',
            index=models.Index(fields=['action', 'timestamp'], name='audit_logs__action_t_idx'),
        ),
        migrations.AddIndex(
            model_name='certificateauditlog',
            index=models.Index(fields=['certificate_id'], name='audit_logs__cert_id_idx'),
        ),
        # Create AlertAuditLog model
        migrations.CreateModel(
            name='AlertAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('create', 'Created'),
                        ('update', 'Updated'),
                        ('resolve', 'Resolved'),
                        ('reopen', 'Reopened'),
                        ('dismiss', 'Dismissed'),
                    ],
                    max_length=20,
                )),
                ('alert_id', models.IntegerField(blank=True, null=True)),
                ('alert_type', models.CharField(blank=True, max_length=100)),
                ('certificate_id', models.IntegerField(blank=True, null=True)),
                ('certificate_name', models.CharField(blank=True, max_length=255)),
                ('old_values', models.JSONField(blank=True, default=dict)),
                ('new_values', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='alertauditlog',
            index=models.Index(fields=['user', 'timestamp'], name='audit_logs__user_id_a_idx'),
        ),
        migrations.AddIndex(
            model_name='alertauditlog',
            index=models.Index(fields=['action', 'timestamp'], name='audit_logs__action_a_idx'),
        ),
        migrations.AddIndex(
            model_name='alertauditlog',
            index=models.Index(fields=['alert_id'], name='audit_logs__alert_id_idx'),
        ),
        migrations.AddIndex(
            model_name='alertauditlog',
            index=models.Index(fields=['certificate_id'], name='audit_logs__cert_id_a_idx'),
        ),
    ]
