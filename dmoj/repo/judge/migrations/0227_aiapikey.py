from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0226_run_submission'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIAPIKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[
                    ('openai', 'OpenAI'),
                    ('gemini', 'Google Gemini'),
                    ('claude', 'Anthropic Claude'),
                    ('deepseek', 'DeepSeek'),
                ], max_length=20, verbose_name='provider')),
                ('key_ciphertext', models.TextField(verbose_name='encrypted API key')),
                ('key_last4', models.CharField(max_length=4, verbose_name='last 4 characters')),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending'),
                    ('verified', 'Verified'),
                    ('failed', 'Failed'),
                ], default='pending', max_length=10, verbose_name='status')),
                ('status_detail', models.TextField(blank=True, default='', verbose_name='status detail')),
                ('default_model', models.CharField(blank=True, default='', max_length=100, verbose_name='default model')),
                ('last_used_at', models.DateTimeField(blank=True, null=True, verbose_name='last used at')),
                ('added_at', models.DateTimeField(auto_now_add=True, verbose_name='added at')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ai_api_keys',
                    to='judge.profile',
                    verbose_name='user',
                )),
            ],
            options={
                'verbose_name': 'AI API key',
                'verbose_name_plural': 'AI API keys',
                'ordering': ['-added_at'],
                'unique_together': {('user', 'provider')},
            },
        ),
        migrations.CreateModel(
            name='AIAPIKeyTestLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[
                    ('openai', 'OpenAI'),
                    ('gemini', 'Google Gemini'),
                    ('claude', 'Anthropic Claude'),
                    ('deepseek', 'DeepSeek'),
                ], max_length=20, verbose_name='provider')),
                ('model_tested', models.CharField(max_length=100, verbose_name='model tested')),
                ('success', models.BooleanField(verbose_name='success')),
                ('detail', models.TextField(blank=True, default='', verbose_name='detail')),
                ('response_time_ms', models.IntegerField(blank=True, null=True, verbose_name='response time (ms)')),
                ('tested_at', models.DateTimeField(auto_now_add=True, verbose_name='tested at')),
                ('api_key', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='test_logs',
                    to='judge.aiapikey',
                    verbose_name='API key',
                )),
            ],
            options={
                'verbose_name': 'API key test log',
                'verbose_name_plural': 'API key test logs',
                'ordering': ['-tested_at'],
            },
        ),
    ]
