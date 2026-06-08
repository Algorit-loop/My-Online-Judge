from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0229_ai_code_review'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIPromptTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(help_text='Unique identifier: ai_problem_creator, ai_code_review, api_key_test', max_length=50, unique=True, verbose_name='key')),
                ('name', models.CharField(help_text='Human-readable name for this prompt', max_length=100, verbose_name='name')),
                ('prompt_text', models.TextField(help_text='The prompt template. Use {variable} for substitution.', verbose_name='prompt text')),
                ('description', models.TextField(blank=True, help_text='Describe what this prompt does and what variables are available.', verbose_name='description')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
            ],
            options={
                'verbose_name': 'AI prompt template',
                'verbose_name_plural': 'AI prompt templates',
                'ordering': ['key'],
            },
        ),
    ]
