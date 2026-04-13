from django.db import migrations, models


def forwards_func(apps, schema_editor):
    """Migrate old partial boolean to new scoring_mode field."""
    Problem = apps.get_model('judge', 'Problem')
    # partial=True → partial_batch (default partial behavior)
    # partial=False → short_circuit
    Problem.objects.filter(partial=True).update(scoring_mode='partial_batch')
    Problem.objects.filter(partial=False).update(scoring_mode='short_circuit')


def reverse_func(apps, schema_editor):
    """Reverse: set partial from scoring_mode."""
    Problem = apps.get_model('judge', 'Problem')
    Problem.objects.filter(scoring_mode='short_circuit').update(partial=False, short_circuit=True)
    Problem.objects.filter(scoring_mode__in=['partial_batch', 'partial_testcase']).update(
        partial=True, short_circuit=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0221_remove_free_credit_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='scoring_mode',
            field=models.CharField(
                choices=[
                    ('short_circuit', 'Short circuit (stop on first failure, all-or-nothing)'),
                    ('partial_batch', 'Partial (by subtask/batch — failed subtask = 0 points)'),
                    ('partial_testcase', 'Partial (by testcase — each correct test earns points)'),
                ],
                default='partial_batch',
                help_text=(
                    'How submissions are scored. Short circuit stops at first wrong answer. '
                    'Partial by subtask gives 0 for a failed subtask. '
                    'Partial by testcase awards points for each correct test within a subtask.'
                ),
                max_length=20,
                verbose_name='scoring mode',
            ),
        ),
        migrations.RunPython(forwards_func, reverse_func),
    ]
