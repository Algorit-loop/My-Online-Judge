# Generated manually to remove free_credit and monthly_free_credit_limit fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0220_submission_total_time'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Drop the actual DB columns:
            # - 'monthly_credit'        (db_column of free_credit, added in 0207)
            # - 'monthly_free_credit_limit' (added in 0212)
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE `judge_organization` DROP COLUMN IF EXISTS `monthly_credit`',
                    reverse_sql='ALTER TABLE `judge_organization` ADD COLUMN `monthly_credit` double NOT NULL DEFAULT 0',
                ),
                migrations.RunSQL(
                    sql='ALTER TABLE `judge_organization` DROP COLUMN IF EXISTS `monthly_free_credit_limit`',
                    reverse_sql='ALTER TABLE `judge_organization` ADD COLUMN `monthly_free_credit_limit` double NOT NULL DEFAULT 10800',
                ),
            ],
            # Update Django's model state to remove both fields.
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
