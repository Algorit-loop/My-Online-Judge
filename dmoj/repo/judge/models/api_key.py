import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from judge.models.profile import Profile

__all__ = ['AIAPIKey', 'AIAPIKeyTestLog']

AI_PROVIDER_CHOICES = [
    ('openai', 'OpenAI'),
    ('gemini', 'Google Gemini'),
    ('claude', 'Anthropic Claude'),
    ('deepseek', 'DeepSeek'),
]

AI_PROVIDER_MODELS = {
    'openai': [
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4o-mini', 'GPT-4o Mini'),
        ('gpt-4.1', 'GPT-4.1'),
        ('gpt-4.1-mini', 'GPT-4.1 Mini'),
        ('gpt-4.1-nano', 'GPT-4.1 Nano'),
        ('o3', 'o3'),
        ('o3-mini', 'o3-mini'),
        ('o4-mini', 'o4-mini'),
    ],
    'gemini': [
        ('gemini-2.5-pro', 'Gemini 2.5 Pro'),
        ('gemini-2.5-flash', 'Gemini 2.5 Flash'),
        ('gemini-2.5-flash-lite', 'Gemini 2.5 Flash-Lite'),
        ('gemini-2.0-flash', 'Gemini 2.0 Flash'),
    ],
    'claude': [
        ('claude-opus-4-7', 'Claude Opus 4.7'),
        ('claude-sonnet-4-6', 'Claude Sonnet 4.6'),
        ('claude-haiku-4-5', 'Claude Haiku 4.5'),
    ],
    'deepseek': [
        ('deepseek-chat', 'DeepSeek-V3'),
        ('deepseek-reasoner', 'DeepSeek-R1'),
    ],
}

AI_PROVIDER_DEFAULT_MODELS = {
    'openai': 'gpt-4o-mini',
    'gemini': 'gemini-2.5-flash',
    'claude': 'claude-sonnet-4-6',
    'deepseek': 'deepseek-chat',
}

STATUS_CHOICES = [
    ('pending', _('Pending')),
    ('verified', _('Verified')),
    ('failed', _('Failed')),
]


def _get_fernet():
    """Derive a Fernet key from Django SECRET_KEY."""
    key_material = ('aiapikey-encryption-' + settings.SECRET_KEY).encode('utf-8')
    derived = hashlib.sha256(key_material).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


class AIAPIKey(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='ai_api_keys',
                             verbose_name=_('user'))
    provider = models.CharField(max_length=20, choices=AI_PROVIDER_CHOICES, verbose_name=_('provider'))
    key_ciphertext = models.TextField(verbose_name=_('encrypted API key'))
    key_last4 = models.CharField(max_length=4, verbose_name=_('last 4 characters'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending',
                              verbose_name=_('status'))
    status_detail = models.TextField(blank=True, default='', verbose_name=_('status detail'))
    default_model = models.CharField(max_length=100, blank=True, default='',
                                     verbose_name=_('default model'))
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name=_('last used at'))
    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_('added at'))

    class Meta:
        verbose_name = _('AI API key')
        verbose_name_plural = _('AI API keys')
        unique_together = ('user', 'provider')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.get_provider_display()} - ****{self.key_last4}'

    def store_key(self, plaintext_key):
        """Encrypt key, store ciphertext and last4. Plaintext is NOT retained."""
        self.key_last4 = plaintext_key[-4:]
        f = _get_fernet()
        self.key_ciphertext = f.encrypt(plaintext_key.encode('utf-8')).decode('ascii')

    def decrypt_key(self):
        """Decrypt and return the API key. ONLY call when actually invoking AI provider."""
        f = _get_fernet()
        try:
            return f.decrypt(self.key_ciphertext.encode('ascii')).decode('utf-8')
        except (InvalidToken, Exception):
            return None


class AIAPIKeyTestLog(models.Model):
    api_key = models.ForeignKey(AIAPIKey, on_delete=models.CASCADE, related_name='test_logs',
                                verbose_name=_('API key'))
    provider = models.CharField(max_length=20, choices=AI_PROVIDER_CHOICES, verbose_name=_('provider'))
    model_tested = models.CharField(max_length=100, verbose_name=_('model tested'))
    success = models.BooleanField(verbose_name=_('success'))
    detail = models.TextField(blank=True, default='', verbose_name=_('detail'))
    response_time_ms = models.IntegerField(null=True, blank=True, verbose_name=_('response time (ms)'))
    tested_at = models.DateTimeField(auto_now_add=True, verbose_name=_('tested at'))

    class Meta:
        verbose_name = _('API key test log')
        verbose_name_plural = _('API key test logs')
        ordering = ['-tested_at']
