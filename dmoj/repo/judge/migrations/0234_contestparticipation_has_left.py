from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0233_seed_ai_gen_code_prompt'),
    ]

    operations = [
        migrations.AddField(
            model_name='contestparticipation',
            name='has_left',
            field=models.BooleanField(
                default=False,
                help_text='Whether this participant has left the contest. '
                          'Once left, the participant cannot rejoin as a live participant.',
                verbose_name='has left contest',
            ),
        ),
    ]
