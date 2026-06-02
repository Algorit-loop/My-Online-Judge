import json
import urllib.error
import urllib.request

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.utils.timezone import now

from judge.models import Language, Problem
from judge.models.api_key import (
    AIAPIKey, AI_PROVIDER_CONFIGS, AI_PROVIDER_MODELS,
)
from judge.models.generate_testcase import GenerateTestcaseJob

_AI_TIMEOUT = 120

GENERATOR_SYSTEM_PROMPT = """You are a competitive programming testcase generator writer.

Return ONLY valid C++17 source code.
Do not use Markdown.
Do not explain anything.

The generator must:
- Generate at most {max_cases} testcase input files.
- Each subtask must have at least one testcase.
- Write files into ./inputs/
- File names: 01.inp, 02.inp, 03.inp, ...
- Never write output files.
- Keep total estimated file size under 128MB.
- Use deterministic randomness with fixed seed.
- Follow the problem input format exactly.
- Respect all constraints from the statement.
- Cover: corner cases, typical cases, stress/large cases, edge cases.

The C++ program must create directory ./inputs if needed (use std::filesystem or mkdir).
"""


def _call_text_api(provider, model, api_key, prompt, system_prompt):
    """Call AI provider with text prompt. Returns (success, text_or_error)."""
    config = AI_PROVIDER_CONFIGS[provider]
    url = config['base_url'] + config['endpoint']
    if '{model}' in url:
        url = url.replace('{model}', model)

    headers = {
        'Content-Type': 'application/json',
        config['auth_header']: config['auth_format'].format(key=api_key),
    }
    headers.update(config.get('extra_headers', {}))

    if provider == 'openai':
        payload = {
            'model': model,
            'input': [{'type': 'input_text', 'text': system_prompt + '\n\n' + prompt}],
        }
    elif provider == 'gemini':
        payload = {
            'contents': [{'parts': [{'text': system_prompt + '\n\n' + prompt}]}],
        }
    elif provider == 'claude':
        payload = {
            'model': model,
            'max_tokens': 8192,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': prompt}],
        }
    elif provider == 'deepseek':
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ],
        }
    else:
        return False, _('Unsupported provider: %s') % provider

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=_AI_TIMEOUT) as resp:
            response_data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            error_body = json.loads(e.read())
            error_msg = error_body.get('error', {}).get('message', str(e))
        except Exception:
            error_msg = str(e)
        return False, _('API error (%d): %s') % (e.code, error_msg)
    except Exception as e:
        return False, _('Connection error: %s') % str(e)

    text = ''
    if provider == 'openai':
        for item in response_data.get('output', []):
            for content in item.get('content', []):
                if content.get('type') == 'output_text':
                    text = content.get('text', '')
                    break
    elif provider == 'gemini':
        candidates = response_data.get('candidates', [])
        parts = candidates[0].get('content', {}).get('parts', []) if candidates else []
        text = parts[0].get('text', '') if parts else ''
    elif provider == 'claude':
        content = response_data.get('content', [])
        text = content[0].get('text', '') if content else ''
    elif provider == 'deepseek':
        choices = response_data.get('choices', [])
        text = choices[0].get('message', {}).get('content', '') if choices else ''

    if not text:
        return False, _('Empty response from AI provider')

    # Strip markdown fences if present
    text = text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        lines = lines[1:]
        if lines and lines[-1].strip().startswith('```'):
            lines = lines[:-1]
        text = '\n'.join(lines).strip()

    return True, text


def _safe_json(s):
    """Escape sequences that could break out of a <script> block."""
    return s.replace('</', r'<\/')


def _serialize_job(job):
    """Serialize a GenerateTestcaseJob to a dict for JSON."""
    return {
        'id': job.id,
        'id_secret': str(job.id_secret),
        'status': job.status,
        'generator_code': job.generator_code,
        'solution_code': job.solution_code,
        'num_cases': job.num_cases,
        'ai_provider': job.ai_provider,
        'ai_model': job.ai_model,
        'error_stage': job.error_stage,
        'error_log': job.error_log[:5000],
        'result_testcases': job.result_testcases,
        'result_zip_size': job.result_zip_size,
    }


# ── Views ──

@login_required
def ai_generate_testcase_view(request, problem):
    """GET — show the Generate Testcase with AI page."""
    problem_obj = get_object_or_404(Problem, code=problem)
    if not problem_obj.is_editable_by(request.user):
        raise Http404()

    languages = Language.objects.filter(file_only=False).order_by('name').values('id', 'name', 'ace', 'key')

    # Find the latest job for this problem by this user
    latest_job = GenerateTestcaseJob.objects.filter(
        problem=problem_obj,
        user=request.user.profile,
    ).order_by('-created_at').first()

    latest_job_json = _safe_json(json.dumps(_serialize_job(latest_job))) if latest_job else 'null'

    return render(request, 'problem/ai_generate_testcase.html', {
        'problem': problem_obj,
        'title': _('Generate Testcase with AI for %s') % problem_obj.name,
        'provider_models_json': _safe_json(json.dumps(AI_PROVIDER_MODELS)),
        'languages_json': _safe_json(json.dumps(list(languages))),
        'latest_job_json': latest_job_json,
        'ACE_URL': settings.ACE_URL,
    })


@login_required
def ai_generate_testcase_process(request, problem):
    """POST — call AI to generate C++ generator code, then create a Draft job."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    problem_obj = get_object_or_404(Problem, code=problem)
    if not problem_obj.is_editable_by(request.user):
        return JsonResponse({'error': _('Permission denied')}, status=403)

    provider = request.POST.get('provider', '').strip()
    model = request.POST.get('model', '').strip()

    if not provider or provider not in AI_PROVIDER_MODELS:
        return JsonResponse({'error': _('Invalid provider')}, status=400)
    if not model or model not in AI_PROVIDER_MODELS.get(provider, []):
        return JsonResponse({'error': _('Invalid model')}, status=400)

    try:
        api_key_obj = AIAPIKey.objects.get(
            user=request.user.profile, provider=provider, status='verified',
        )
    except AIAPIKey.DoesNotExist:
        return JsonResponse({
            'error': _('No verified API key found for %s. Please add and verify one first.') % provider,
        }, status=400)

    plaintext_key = api_key_obj.decrypt_key()
    if not plaintext_key:
        return JsonResponse({'error': _('Failed to decrypt API key')}, status=500)

    max_cases = int(request.POST.get('num_cases', '20'))
    max_cases = max(1, min(40, max_cases))

    system_prompt = GENERATOR_SYSTEM_PROMPT.replace('{max_cases}', str(max_cases))

    user_prompt = '## Problem Statement\n\n' + (problem_obj.description or '(no description)')
    user_prompt += '\n\nGenerate a C++ generator that creates exactly %d input files.' % max_cases

    success, result = _call_text_api(provider, model, plaintext_key, user_prompt, system_prompt)
    plaintext_key = None  # noqa: F841

    if not success:
        return JsonResponse({'error': result}, status=400)

    api_key_obj.last_used_at = now()
    api_key_obj.save(update_fields=['last_used_at'])

    # Save as Draft job (delete old drafts for this problem+user first)
    solution_code = request.POST.get('solution_code', '').strip()

    GenerateTestcaseJob.objects.filter(
        problem=problem_obj, user=request.user.profile, status='DR',
    ).delete()

    job = GenerateTestcaseJob.objects.create(
        problem=problem_obj,
        user=request.user.profile,
        status='DR',
        generator_code=result,
        solution_code=solution_code,
        num_cases=max_cases,
        ai_provider=provider,
        ai_model=model,
    )

    return JsonResponse({
        'success': True,
        'generator_code': result,
        'job_id': job.id,
        'id_secret': str(job.id_secret),
    })


@login_required
def ai_generate_testcase_apply(request, problem):
    """POST — create a job and kick off the Celery pipeline. Returns {job_id, id_secret}."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    problem_obj = get_object_or_404(Problem, code=problem)
    if not problem_obj.is_editable_by(request.user):
        return JsonResponse({'error': _('Permission denied')}, status=403)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': _('Invalid request body')}, status=400)

    generator_code = body.get('generator_code', '').strip()
    solution_code = body.get('solution_code', '').strip()
    try:
        num_cases = max(1, min(40, int(body.get('num_cases', 20))))
    except (ValueError, TypeError):
        num_cases = 20

    if not generator_code:
        return JsonResponse({'error': _('Generator code is required')}, status=400)
    if not solution_code:
        return JsonResponse({'error': _('Solution code is required')}, status=400)

    # Always create a new job (becomes the latest; old draft is superseded)
    job = GenerateTestcaseJob.objects.create(
        problem=problem_obj,
        user=request.user.profile,
        generator_code=generator_code,
        solution_code=solution_code,
        num_cases=num_cases,
        ai_provider=body.get('provider', ''),
        ai_model=body.get('model', ''),
    )

    from judge.tasks.generate_testcase import run_generate_testcase
    run_generate_testcase.delay(job.id)

    return JsonResponse({
        'success': True,
        'job_id': job.id,
        'id_secret': str(job.id_secret),
    })


@login_required
def ai_generate_testcase_poll(request, problem):
    """GET — poll job status (fallback if wsevent is down)."""
    problem_obj = get_object_or_404(Problem, code=problem)
    if not problem_obj.is_editable_by(request.user):
        return JsonResponse({'error': _('Permission denied')}, status=403)

    job_id = request.GET.get('job_id')
    if not job_id:
        return JsonResponse({'error': 'Missing job_id'}, status=400)

    try:
        job = GenerateTestcaseJob.objects.get(id=job_id, problem=problem_obj)
    except GenerateTestcaseJob.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

    data = {
        'status': job.status,
        'status_display': job.get_status_display(),
    }
    if job.status == 'ER':
        data['error_stage'] = job.error_stage
        data['error_log'] = job.error_log
    elif job.status == 'DN':
        data['result_testcases'] = job.result_testcases
        data['result_zip_size'] = job.result_zip_size

    return JsonResponse(data)
