
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("judge", "0236_add_user_problem_tag"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userproblemtag",
            name="submission",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_tags",
                to="judge.submission",
                verbose_name="source submission",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="userproblemtag",
            unique_together={("user", "submission", "tag")},
        ),
    ]
