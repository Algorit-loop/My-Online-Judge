import json
import time
import urllib.request
import urllib.error

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from judge.models.ai_prompt import AIPromptTemplate
from judge.models.api_key import (
    AIAPIKey, AIAPIKeyTestLog,
    AI_PROVIDER_CHOICES, AI_PROVIDER_MODELS, AI_PROVIDER_DEFAULT_MODELS, AI_PROVIDER_CONFIGS,
)

_DEFAULT_API_TEST_PROMPT = 'Reply exactly: OK'
from judge.views.user import UserPage


class APIKeyPageView(UserPage):
    template_name = 'user/api-keys.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('AI API Keys')
        context['content_title'] = _('AI API Keys')
        context['tab'] = 'api_keys'
        context['providers'] = AI_PROVIDER_CHOICES
        context['provider_models_json'] = json.dumps(AI_PROVIDER_MODELS)
        return context


@login_required
def api_key_list(request):
    """Return user's API keys as JSON. Never returns plaintext key."""
    keys = AIAPIKey.objects.filter(user=request.profile)
    data = []
    for key in keys:
        data.append({
            'id': key.id,
            'provider': key.provider,
            'provider_display': key.get_provider_display(),
            'key_last4': key.key_last4,
            'status': key.status,
            'status_display': key.get_status_display(),
            'status_detail': key.status_detail,
            'default_model': key.default_model,
            'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
            'added_at': key.added_at.isoformat(),
        })
    return JsonResponse({'keys': data})


@login_required
@require_POST
def api_key_add(request):
    """Add or update an API key for a provider. Stores encrypted, returns only last4."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Invalid request data')}, status=400)

    provider = data.get('provider', '').strip()
    api_key_value = data.get('api_key', '').strip()

    if not provider or not api_key_value:
        return JsonResponse({'error': _('Provider and API key are required')}, status=400)

    valid_providers = [p[0] for p in AI_PROVIDER_CHOICES]
    if provider not in valid_providers:
        return JsonResponse({'error': _('Invalid provider')}, status=400)

    if len(api_key_value) < 10:
        return JsonResponse({'error': _('API key too short')}, status=400)

    if len(api_key_value) > 512:
        return JsonResponse({'error': _('API key too long')}, status=400)

    default_model = AI_PROVIDER_DEFAULT_MODELS.get(provider, '')

    try:
        obj = AIAPIKey.objects.get(user=request.profile, provider=provider)
        obj.store_key(api_key_value)
        obj.status = 'pending'
        obj.status_detail = ''
        obj.default_model = default_model
        obj.save()
    except AIAPIKey.DoesNotExist:
        obj = AIAPIKey(user=request.profile, provider=provider,
                       default_model=default_model, status='pending')
        obj.store_key(api_key_value)
        obj.save()

    # Wipe plaintext reference
    api_key_value = None  # noqa: F841

    return JsonResponse({
        'id': obj.id,
        'provider': obj.provider,
        'provider_display': obj.get_provider_display(),
        'key_last4': obj.key_last4,
        'status': obj.status,
        'status_display': obj.get_status_display(),
        'default_model': obj.default_model,
    })


@login_required
@require_POST
def api_key_delete(request, key_id):
    """Delete an API key and its test logs."""
    try:
        key = AIAPIKey.objects.get(id=key_id, user=request.profile)
    except AIAPIKey.DoesNotExist:
        return JsonResponse({'error': _('API key not found')}, status=404)
    key.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def api_key_test(request, key_id):
    """Test API key connection. Decrypts key only for this call, then discards."""
    try:
        key = AIAPIKey.objects.get(id=key_id, user=request.profile)
    except AIAPIKey.DoesNotExist:
        return JsonResponse({'error': _('API key not found')}, status=404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        body = {}

    model = body.get('model', '').strip()
    if not model:
        model = key.default_model or AI_PROVIDER_DEFAULT_MODELS.get(key.provider, '')

    valid_models = AI_PROVIDER_MODELS.get(key.provider, [])
    if model not in valid_models:
        return JsonResponse({'error': _('Invalid model for this provider')}, status=400)

    test_func = _PROVIDER_TEST_FUNCS.get(key.provider)
    if not test_func:
        return JsonResponse({'error': _('Provider not supported')}, status=400)

    # Decrypt only here, use immediately, then discard
    plaintext = key.decrypt_key()
    if not plaintext:
        return JsonResponse({'error': _('Failed to decrypt API key')}, status=500)

    start = time.time()
    try:
        success, detail = test_func(plaintext, model)
    except Exception as e:
        success = False
        detail = str(e)
    finally:
        plaintext = None  # noqa: F841
    elapsed_ms = int((time.time() - start) * 1000)

    # Update key status
    key.status = 'verified' if success else 'failed'
    key.status_detail = '' if success else detail
    if success:
        key.last_used_at = timezone.now()
    key.save(update_fields=['status', 'status_detail', 'last_used_at'])

    # Log
    log = AIAPIKeyTestLog.objects.create(
        api_key=key, provider=key.provider, model_tested=model, success=success,
        detail=detail, response_time_ms=elapsed_ms,
    )

    return JsonResponse({
        'success': success,
        'status': key.status,
        'status_display': key.get_status_display(),
        'detail': detail,
        'log': {
            'id': log.id,
            'provider': log.provider,
            'provider_display': key.get_provider_display(),
            'model_tested': log.model_tested,
            'success': log.success,
            'detail': log.detail,
            'response_time_ms': log.response_time_ms,
            'tested_at': log.tested_at.isoformat(),
        },
    })


@login_required
def api_key_logs(request, key_id):
    """Return test logs for a specific API key."""
    try:
        key = AIAPIKey.objects.get(id=key_id, user=request.profile)
    except AIAPIKey.DoesNotExist:
        return JsonResponse({'error': _('API key not found')}, status=404)

    logs = AIAPIKeyTestLog.objects.filter(api_key=key).order_by('-tested_at')[:50]
    data = [{
        'id': l.id,
        'provider': key.provider,
        'provider_display': key.get_provider_display(),
        'model_tested': l.model_tested,
        'success': l.success,
        'detail': l.detail,
        'response_time_ms': l.response_time_ms,
        'tested_at': l.tested_at.isoformat(),
    } for l in logs]
    return JsonResponse({'logs': data})


@login_required
def api_key_all_logs(request):
    """Return all test logs for the current user, across all keys (max 50 recent)."""
    logs = (AIAPIKeyTestLog.objects
            .filter(api_key__user=request.profile)
            .select_related('api_key')
            .order_by('-tested_at')[:50])
    data = [{
        'id': l.id,
        'provider': l.api_key.provider,
        'provider_display': l.api_key.get_provider_display(),
        'model_tested': l.model_tested,
        'success': l.success,
        'detail': l.detail,
        'response_time_ms': l.response_time_ms,
        'tested_at': l.tested_at.isoformat(),
    } for l in logs]
    return JsonResponse({'logs': data})


# === Provider test functions ===
# Timeout is set to 90s because thinking/reasoning models (o3, DeepSeek-R1, etc.)
# can take 60s+ before responding.
_API_TEST_TIMEOUT = 90


def _get_test_prompt():
    return AIPromptTemplate.get_prompt('api_key_test', _DEFAULT_API_TEST_PROMPT)


def _test_openai(api_key, model):
    """OpenAI Responses API: POST /v1/responses with {model, input}."""
    config = AI_PROVIDER_CONFIGS['openai']
    url = config['base_url'] + config['endpoint']
    headers = {
        'Content-Type': 'application/json',
        config['auth_header']: config['auth_format'].format(key=api_key),
    }
    payload = json.dumps({
        'model': model,
        'input': _get_test_prompt(),
    }).encode()
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_API_TEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
            if 'output' not in data and 'id' not in data:
                return False, _('Unexpected response format')
            return True, _('Connection successful')
    except urllib.error.HTTPError as e:
        return False, _parse_http_error(e)
    except Exception as e:
        return False, _('Connection error: %s') % str(e)


def _test_gemini(api_key, model):
    """Gemini API: POST /v1beta/models/{model}:generateContent, auth via x-goog-api-key header."""
    config = AI_PROVIDER_CONFIGS['gemini']
    url = config['base_url'] + config['endpoint'].format(model=model)
    headers = {
        'Content-Type': 'application/json',
        config['auth_header']: config['auth_format'].format(key=api_key),
    }
    payload = json.dumps({
        'contents': [{'parts': [{'text': _get_test_prompt()}]}],
    }).encode()
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_API_TEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
            if 'candidates' not in data:
                return False, _('Unexpected response format')
            return True, _('Connection successful')
    except urllib.error.HTTPError as e:
        return False, _parse_http_error(e)
    except Exception as e:
        return False, _('Connection error: %s') % str(e)


def _test_claude(api_key, model):
    """Claude API: POST /v1/messages with {model, messages, max_tokens}, auth via x-api-key header."""
    config = AI_PROVIDER_CONFIGS['claude']
    url = config['base_url'] + config['endpoint']
    headers = {
        'Content-Type': 'application/json',
        config['auth_header']: config['auth_format'].format(key=api_key),
    }
    headers.update(config.get('extra_headers', {}))
    payload = json.dumps({
        'model': model,
        'max_tokens': 128,
        'messages': [{'role': 'user', 'content': _get_test_prompt()}],
    }).encode()
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_API_TEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
            if 'content' not in data:
                return False, _('Unexpected response format')
            return True, _('Connection successful')
    except urllib.error.HTTPError as e:
        return False, _parse_http_error(e)
    except Exception as e:
        return False, _('Connection error: %s') % str(e)


def _test_deepseek(api_key, model):
    """DeepSeek API: POST /chat/completions with {model, messages}, auth via Bearer token."""
    config = AI_PROVIDER_CONFIGS['deepseek']
    url = config['base_url'] + config['endpoint']
    headers = {
        'Content-Type': 'application/json',
        config['auth_header']: config['auth_format'].format(key=api_key),
    }
    payload = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': _get_test_prompt()}],
    }).encode()
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_API_TEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
            if 'choices' not in data:
                return False, _('Unexpected response format')
            return True, _('Connection successful')
    except urllib.error.HTTPError as e:
        return False, _parse_http_error(e)
    except Exception as e:
        return False, _('Connection error: %s') % str(e)


def _parse_http_error(e):
    """Parse HTTP error into user-friendly message."""
    try:
        body = e.read().decode('utf-8', errors='replace')
        data = json.loads(body)
        msg = data.get('error', {}).get('message', '') or str(e)
    except Exception:
        msg = str(e)
    if e.code == 401:
        return _('Invalid API key')
    elif e.code == 403:
        return _('No permission')
    elif e.code == 404:
        return _('Model not found')
    elif e.code == 429:
        return _('Rate limited, try later')
    return f'HTTP {e.code}: {msg}'


_PROVIDER_TEST_FUNCS = {
    'openai': _test_openai,
    'gemini': _test_gemini,
    'claude': _test_claude,
    'deepseek': _test_deepseek,
}
