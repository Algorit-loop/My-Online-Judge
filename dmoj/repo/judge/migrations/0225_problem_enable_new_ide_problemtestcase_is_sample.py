from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0224_contest_penalty_time_format'),  # Update this to the actual last migration
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='enable_new_ide',
            field=models.BooleanField(
                default=False,
                help_text='Enable the new IDE layout with code editor and custom testcase runner.',
                verbose_name='Bật giao diện IDE mới',
            ),
        ),
        migrations.AddField(
            model_name='problemtestcase',
            name='is_sample',
            field=models.BooleanField(default=False, verbose_name='sample testcase?'),
        ),
    ]
