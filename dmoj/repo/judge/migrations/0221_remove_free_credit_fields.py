# Generated manually to remove free_credit and monthly_free_credit_limit fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0220_submission_total_time'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Both columns don't exist in the DB, skip all DB operations.
            database_operations=[],
            # Only update Django's model state to remove both fields.
            state_operations=[
                migrations.RemoveField(
                    model_name='organization',
                    name='free_credit',
                ),
                migrations.RemoveField(
                    model_name='organization',
                    name='monthly_free_credit_limit',
                ),
            ],
        ),
    ]
