from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0227_aiapikey'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='enable_focus_lock',
            field=models.BooleanField(
                default=False,
                help_text='Hide navbar, request fullscreen, and track tab/fullscreen violations for live participants.',
                verbose_name='enable focus lock',
            ),
        ),
        migrations.AddField(
            model_name='contestparticipation',
            name='focus_violations',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Number of times the participant exited fullscreen or switched tabs.',
                verbose_name='focus violations',
            ),
        ),
    ]
