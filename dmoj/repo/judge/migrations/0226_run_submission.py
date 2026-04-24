from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0225_problem_enable_new_ide_problemtestcase_is_sample'),
    ]

    operations = [
        migrations.CreateModel(
            name='RunSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='submission time')),
                ('time', models.FloatField(null=True, verbose_name='execution time')),
                ('memory', models.FloatField(null=True, verbose_name='memory usage')),
                ('points', models.FloatField(null=True, verbose_name='points granted')),
                ('status', models.CharField(choices=[('QU', 'Queued'), ('P', 'Processing'), ('G', 'Grading'), ('D', 'Completed'), ('IE', 'Internal Error'), ('CE', 'Compile Error'), ('AB', 'Aborted')], default='QU', max_length=2, verbose_name='status')),
                ('result', models.CharField(blank=True, choices=[('AC', 'Accepted'), ('WA', 'Wrong Answer'), ('TLE', 'Time Limit Exceeded'), ('MLE', 'Memory Limit Exceeded'), ('OLE', 'Output Limit Exceeded'), ('IR', 'Invalid Return'), ('RTE', 'Runtime Error'), ('CE', 'Compile Error'), ('IE', 'Internal Error'), ('SC', 'Short Circuited'), ('AB', 'Aborted')], default=None, max_length=3, null=True, verbose_name='result')),
                ('error', models.TextField(blank=True, null=True, verbose_name='compile errors')),
                ('current_testcase', models.IntegerField(default=0)),
                ('batch', models.BooleanField(default=False, verbose_name='batched cases')),
                ('case_points', models.FloatField(default=0, verbose_name='test case points')),
                ('case_total', models.FloatField(default=0, verbose_name='test case total points')),
                ('judged_date', models.DateTimeField(default=None, null=True, verbose_name='submission judge time')),
                ('source', models.TextField(max_length=65536, verbose_name='source code')),
                ('case_results', models.JSONField(blank=True, default=list, verbose_name='test case results')),
                ('judged_on', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='judge.judge', verbose_name='judged on')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='judge.language', verbose_name='submission language')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='judge.problem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='judge.profile')),
            ],
            options={
                'verbose_name': 'run submission',
                'verbose_name_plural': 'run submissions',
            },
        ),
    ]
