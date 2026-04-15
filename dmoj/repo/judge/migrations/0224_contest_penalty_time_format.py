from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0223_contest_problem_label_style'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='penalty_time_format',
            field=models.CharField(
                choices=[('hh:mm:ss', 'HH:MM:SS'), ('mm', 'Minutes')],
                default='hh:mm:ss',
                help_text='Display format for solving time in the ranking table.',
                max_length=10,
                verbose_name='penalty time format',
            ),
        ),
    ]
