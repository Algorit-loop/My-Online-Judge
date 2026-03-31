from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('judge', '0219_problemdata_zipfile_size_alter_contest_authors_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='total_time',
            field=models.FloatField(null=True, verbose_name='total execution time'),
        ),
    ]
