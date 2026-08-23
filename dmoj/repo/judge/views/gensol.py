import json
import logging

from django.conf import settings
from django.db import transaction
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from judge.models import Problem, Language
from judge.models.ai_gen_code import AIGenCode
from judge.models.api_key import AI_PROVIDER_MODELS
from judge.models.gensol_job import GensolJob, GENSOL_IN_PROGRESS_STATUSES
from judge.models.problem_data import ProblemTestCase

logger = logging.getLogger('judge.gensol')


def _safe_json(s):
    return s.replace('</', r'<\/')


def _get_displayed_generator_source(problem_obj, latest_job=None):
    """Generator source the page puts in the editor: the most recent AI generation, else the
    generator from the last job.
    """
    if latest_job is None:
        latest_job = GensolJob.objects.filter(problem=problem_obj).order_by('-created_date').first()

    latest_gen_code = AIGenCode.objects.filter(problem=problem_obj).order_by('-created_at').first()
    if latest_gen_code and (not latest_job or latest_gen_code.created_at > latest_job.created_date):
        return latest_gen_code.generated_code
    if latest_job:
        return latest_job.generator_source
    return None


def _normalize_source(source):
    """Normalize before comparing: ACE rewrites line endings and the client trims before POSTing,
    so those differences are not meaningful edits.
    """
    return (source or '').replace('\r\n', '\n').replace('\r', '\n').strip()


def _is_allowed_generator_source(problem_obj, source):
    """Whether a non-superuser may start a job with this generator.

    The rule being enforced is "you did not hand-write it", not "it is the newest one", so this accepts
    any generator the problem has legitimately had: every AI generation, plus the last job's. Comparing
    against only the single most recent source would 403 an editor who loaded the page before a
    co-editor pressed "Generate with AI" — and the error message would blame them for an edit they
    never made. AIGenCode is deliberately not filtered by user: co-editors share one problem, and each
    other's AI output is already what the editor shows them.
    """
    candidate = _normalize_source(source)
    if not candidate:
        return False

    ai_sources = AIGenCode.objects.filter(problem=problem_obj).values_list('generated_code', flat=True)
    if any(candidate == _normalize_source(code) for code in ai_sources):
        return True

    last_job_source = (GensolJob.objects.filter(problem=problem_obj)
                       .order_by('-created_date').values_list('generator_source', flat=True).first())
    return last_job_source is not None and candidate == _normalize_source(last_job_source)


@login_required
def generate_testcase_view(request, problem):
    problem_obj = get_object_or_404(Problem, code=problem)
    if not (problem_obj.is_editable_by(request.user)
            and request.user.has_perm('judge.generate_testcase_ai')):
        raise Http404()

    languages = list(
        Language.objects.filter(file_only=False)
        .order_by('name')
        .values_list('key', 'name')
    )

    latest_job = GensolJob.objects.filter(
        problem=problem_obj,
    ).select_related('solution_language', 'generator_language').order_by('-created_date').first()

    # Generator source: prefer AIGenCode (most recent AI generation), fall back to GensolJob
    saved_generator = _get_displayed_generator_source(problem_obj, latest_job)

    # Zip size for a completed job, so a page reload can still show it (see gensol.py _finalize_job
    # for the live value posted over the websocket during an active run).
    zip_size_mb = None
    if latest_job and latest_job.status == 'DONE' and hasattr(problem_obj, 'data_files'):
        zip_size_mb = round(problem_obj.data_files.zipfile_size / 1024 / 1024, 2)

    ctx = {
        'problem': problem_obj,
        'title': _('Generate Testcase for %s') % problem_obj.name,
        'content_title': mark_safe(escape(_('Generate Testcase for %s')) % format_html(
            '<a href="{1}">{0}</a>', problem_obj.name,
            reverse('problem_detail', args=[problem_obj.code]))),
        'ACE_URL': settings.ACE_URL,
        'languages': languages,
        'provider_models_json': _safe_json(json.dumps(AI_PROVIDER_MODELS)),
        'gensol_job': latest_job,
        'saved_generator_source': _safe_json(json.dumps(saved_generator)) if saved_generator else 'null',
        'saved_solution_source': _safe_json(json.dumps(latest_job.solution_source)) if latest_job else 'null',
        'saved_solution_language': latest_job.solution_language.key if latest_job else '',
        'saved_num_cases': latest_job.num_cases if latest_job else 20,
        # JSON-encoded (not raw-interpolated) because this is free-form text that can contain a compiler
        # log — quotes/newlines/backslashes would otherwise break the inline <script> below.
        'saved_error_message': _safe_json(json.dumps(latest_job.error_message)) if latest_job else 'null',
        'zip_size_mb_json': json.dumps(zip_size_mb),
    }

    return render(request, 'problem/generate_testcase.html', ctx)


class GensolStartView(LoginRequiredMixin, View):
    def post(self, request, problem):
        problem_obj = get_object_or_404(Problem, code=problem)
        if not (problem_obj.is_editable_by(request.user)
                and request.user.has_perm('judge.generate_testcase_ai')):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        if problem_obj.is_manually_managed:
            return JsonResponse({'error': 'Problem is manually managed'}, status=400)

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Validate required fields
        generator_source = data.get('generator_source', '').strip()
        solution_source = data.get('solution_source', '').strip()
        generator_language = data.get('generator_language', '')
        solution_language = data.get('solution_language', '')
        num_cases = data.get('num_cases', 0)
        confirm_overwrite = data.get('confirm_overwrite', False)

        if not generator_source:
            return JsonResponse({'error': 'Generator source is required'}, status=400)
        if not solution_source:
            return JsonResponse({'error': 'Solution source is required'}, status=400)
        if not generator_language:
            return JsonResponse({'error': 'Generator language is required'}, status=400)
        if not solution_language:
            return JsonResponse({'error': 'Solution language is required'}, status=400)
        if not isinstance(num_cases, int) or num_cases < 1 or num_cases > 50:
            return JsonResponse({'error': 'Number of cases must be between 1 and 50'}, status=400)

        # The generator editor is read-only for non-superusers (see generate_testcase.html), so
        # enforce that here too — otherwise the restriction is trivially bypassed by POSTing a
        # hand-edited generator. They may still change it through "Generate with AI", which stores
        # an AIGenCode row that _get_displayed_generator_source() then returns.
        if not request.user.is_superuser:
            if not _is_allowed_generator_source(problem_obj, generator_source):
                return JsonResponse({
                    'error': 'You are not allowed to edit the generator code. '
                             'Use "Generate with AI" to change it.',
                }, status=403)

        # Validate languages
        try:
            gen_lang = Language.objects.get(key=generator_language)
        except Language.DoesNotExist:
            return JsonResponse({'error': 'Invalid generator language'}, status=400)
        try:
            sol_lang = Language.objects.get(key=solution_language)
        except Language.DoesNotExist:
            return JsonResponse({'error': 'Invalid solution language'}, status=400)

        # Check for existing testcases (outside transaction - read-only check)
        has_testcases = ProblemTestCase.objects.filter(dataset=problem_obj).exists()
        if has_testcases and not confirm_overwrite:
            return JsonResponse({
                'error': 'confirm_overwrite_required',
                'message': 'Problem already has testcases. Set confirm_overwrite=true to overwrite.',
            }, status=409)

        # Check for in-progress jobs and create atomically to prevent race conditions
        with transaction.atomic():
            active_jobs = (GensolJob.objects.select_for_update()
                           .filter(problem=problem_obj, status__in=GENSOL_IN_PROGRESS_STATUSES))
            if active_jobs.exists():
                return JsonResponse({'error': 'A generation job is already in progress'}, status=409)

            job = GensolJob.objects.create(
                problem=problem_obj,
                user=request.profile,
                generator_source=generator_source,
                generator_language=gen_lang,
                solution_source=solution_source,
                solution_language=sol_lang,
                num_cases=num_cases,
            )

        # Start the job (creates virtual testcases and dispatches to judge)
        from judge.utils.gensol import start_gensol_job
        start_gensol_job(job)

        # Check if job failed during startup (e.g. bridge down, zip error)
        job.refresh_from_db()
        if job.status == 'ERROR':
            return JsonResponse({
                'error': job.error_message or 'Failed to start generation job',
            }, status=500)

        return JsonResponse({
            'job_id': job.id,
            'id_secret': job.id_secret,
        })


