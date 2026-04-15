from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0222_problem_scoring_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='problem_label_style',
            field=models.CharField(
                choices=[('numeric', 'Numeric (1, 2, 3, \u2026)'), ('alphabetic', 'Alphabetic (A, B, C, \u2026)')],
                default='numeric',
                max_length=10,
                verbose_name='problem label style',
            ),
        ),
    ]
