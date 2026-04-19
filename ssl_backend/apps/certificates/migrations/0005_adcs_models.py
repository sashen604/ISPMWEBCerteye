# Generated migration for AD CS models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0004_certificate_risk_reasoning'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ADCSSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_name', models.CharField(help_text='Friendly name for this AD CS source', max_length=255, unique=True)),
                ('description', models.TextField(blank=True, help_text='Description of this AD CS server')),
                ('server_hostname', models.CharField(help_text='FQDN or IP address of AD CS server', max_length=255)),
                ('server_ip', models.CharField(help_text='IPv4 or IPv6 address of AD CS server', max_length=45)),
                ('ca_name', models.CharField(help_text='Common Name of the Certificate Authority', max_length=255)),
                ('domain', models.CharField(help_text='NETBIOS domain or DNS domain', max_length=255)),
                ('username', models.CharField(max_length=255)),
                ('encrypted_password', models.TextField(help_text='Encrypted service account password')),
                ('auth_type', models.CharField(choices=[('winrm', 'WinRM PowerShell'), ('ldap', 'LDAP Query'), ('agent', 'Local Agent')], default='winrm', max_length=20)),
                ('port', models.PositiveIntegerField(default=5985, help_text='WinRM port (5985=HTTP, 5986=HTTPS)')),
                ('use_ssl', models.BooleanField(default=True, help_text='Use HTTPS for WinRM connection')),
                ('verify_ssl', models.BooleanField(default=True, help_text='Verify SSL certificate')),
                ('connection_status', models.CharField(choices=[('connected', 'Connected'), ('disconnected', 'Disconnected'), ('error', 'Connection Error'), ('untested', 'Not Tested')], default='untested', max_length=50)),
                ('last_connection_at', models.DateTimeField(blank=True, help_text='Last successful connection time', null=True)),
                ('connection_error', models.TextField(blank=True, help_text='Last connection error message')),
                ('auto_sync_enabled', models.BooleanField(default=True, help_text='Enable automatic daily sync')),
                ('sync_interval_hours', models.PositiveIntegerField(default=24, help_text='Hours between automatic syncs')),
                ('last_sync_at', models.DateTimeField(blank=True, help_text='Last successful sync time', null=True)),
                ('certificate_count', models.PositiveIntegerField(default=0, help_text='Number of certificates currently stored from this source')),
                ('is_active', models.BooleanField(default=True, help_text='Active sources appear in dashboard')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='adcs_sources_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ADCSSyncHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_type', models.CharField(choices=[('manual', 'Manual'), ('scheduled', 'Scheduled'), ('on_demand', 'On-Demand')], default='manual', max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('success', 'Success'), ('partial_success', 'Partial Success'), ('failed', 'Failed')], default='pending', max_length=50)),
                ('certificates_fetched', models.PositiveIntegerField(default=0)),
                ('certificates_imported', models.PositiveIntegerField(default=0)),
                ('certificates_updated', models.PositiveIntegerField(default=0)),
                ('certificates_failed', models.PositiveIntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
                ('sync_details', models.JSONField(blank=True, default=dict, help_text='Detailed sync information')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, help_text='When sync completed', null=True)),
                ('duration_seconds', models.PositiveIntegerField(blank=True, help_text='Total sync duration in seconds', null=True)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_history', to='certificates.adcssource')),
                ('triggered_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='ADCSConnectionTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('test_results', models.JSONField(help_text='Detailed test results')),
                ('overall_status', models.CharField(choices=[('connected', 'Connected'), ('failed', 'Failed'), ('partial', 'Partial')], max_length=50)),
                ('message', models.TextField()),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connection_tests', to='certificates.adcssource')),
                ('tested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ADCSCredentialHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_type', models.CharField(choices=[('password_updated', 'Password Updated'), ('username_updated', 'Username Updated'), ('auth_type_changed', 'Auth Type Changed')], max_length=50)),
                ('password_hash', models.CharField(help_text='SHA256 hash of old password for audit', max_length=255)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.CharField(blank=True, max_length=45)),
                ('changed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credential_history', to='certificates.adcssource')),
            ],
            options={
                'ordering': ['-changed_at'],
            },
        ),
        migrations.CreateModel(
            name='ADCSCertificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_id', models.CharField(help_text='AD CS request ID', max_length=50, unique=True)),
                ('template_name', models.CharField(help_text='Certificate template used', max_length=255)),
                ('requester', models.CharField(blank=True, help_text='User or machine that requested cert', max_length=255)),
                ('approver', models.CharField(blank=True, help_text='User who approved the request', max_length=255)),
                ('status_code', models.PositiveIntegerField(default=0, help_text='AD CS status code')),
                ('dns_names', models.JSONField(default=list, help_text='List of DNS names/SANs')),
                ('issued_at', models.DateTimeField(help_text='When certificate was issued')),
                ('renewed_at', models.DateTimeField(blank=True, help_text='When certificate was last renewed', null=True)),
                ('revoked_at', models.DateTimeField(blank=True, help_text='When certificate was revoked (if applicable)', null=True)),
                ('imported_at', models.DateTimeField(auto_now_add=True)),
                ('last_verified_at', models.DateTimeField(blank=True, null=True)),
                ('certificate', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='adcs_metadata', to='certificates.certificate')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='certificates.adcssource')),
            ],
            options={
                'ordering': ['-issued_at'],
            },
        ),
        migrations.AddIndex(
            model_name='adcssource',
            index=models.Index(fields=['is_active', 'ca_name'], name='certificates_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='adcssource',
            index=models.Index(fields=['connection_status'], name='certificates_connect_idx'),
        ),
        migrations.AddIndex(
            model_name='adcssource',
            index=models.Index(fields=['last_sync_at'], name='certificates_last_sy_idx'),
        ),
        migrations.AddIndex(
            model_name='adcssynchistory',
            index=models.Index(fields=['source', '-started_at'], name='certificates_source_sta_idx'),
        ),
        migrations.AddIndex(
            model_name='adcssynchistory',
            index=models.Index(fields=['status'], name='certificates_status_idx'),
        ),
        migrations.AddIndex(
            model_name='adcsconnectiontest',
            index=models.Index(fields=['source', '-created_at'], name='certificates_source_cre_idx'),
        ),
        migrations.AddIndex(
            model_name='adcscredentialhistory',
            index=models.Index(fields=['source', '-changed_at'], name='certificates_source_cha_idx'),
        ),
        migrations.AddIndex(
            model_name='adcscertificate',
            index=models.Index(fields=['source', 'template_name'], name='certificates_source_tem_idx'),
        ),
        migrations.AddIndex(
            model_name='adcscertificate',
            index=models.Index(fields=['request_id'], name='certificates_request_idx'),
        ),
    ]
