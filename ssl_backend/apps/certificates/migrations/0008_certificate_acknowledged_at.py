from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("certificates", "0007_domain_domainscanhistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="certificate",
            name="acknowledged_at",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text="When an operator acknowledged review of this certificate (internal workflow).",
                null=True,
            ),
        ),
    ]
