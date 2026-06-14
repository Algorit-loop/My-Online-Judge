import json
import logging

from django.conf import settings
from django.db import transaction
from django.http import Http404, JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from judge.models import Problem, Language
from judge.models.api_key import AI_PROVIDER_MODELS
from judge.models.gensol_job import GensolJob, GENSOL_IN_PROGRESS_STATUSES
from judge.models.problem_data import ProblemTestCase

logger = logging.getLogger('judge.gensol')


def _safe_json(s):
    return s.replace('</', r'<\/')


@login_required
def generate_testcase_view(request, problem):
    problem_obj = get_object_or_404(Problem, code=problem)
    if not problem_obj.is_editable_by(request.user):
        raise Http404()

    languages = list(
        Language.objects.filter(file_only=False)
        .order_by('name')
        .values_list('key', 'name')
    )

    latest_job = GensolJob.objects.filter(
        problem=problem_obj,
    ).select_related('solution_language', 'generator_language').order_by('-created_date').first()

    ctx = {
        'problem': problem_obj,
        'title': _('Generate Testcase for %s') % problem_obj.name,
        'ACE_URL': settings.ACE_URL,
        'languages': languages,
        'provider_models_json': _safe_json(json.dumps(AI_PROVIDER_MODELS)),
        'gensol_job': latest_job,
        'saved_generator_source': _safe_json(json.dumps(latest_job.generator_source)) if latest_job else 'null',
        'saved_solution_source': _safe_json(json.dumps(latest_job.solution_source)) if latest_job else 'null',
        'saved_solution_language': latest_job.solution_language.key if latest_job else '',
        'saved_num_cases': latest_job.num_cases if latest_job else 20,
    }

    return render(request, 'problem/generate_testcase.html', ctx)


class GensolStartView(LoginRequiredMixin, View):
    def post(self, request, problem):
        problem_obj = get_object_or_404(Problem, code=problem)
        if not (request.user.is_superuser or problem_obj.is_editable_by(request.user)):
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

        return JsonResponse({
            'job_id': job.id,
            'id_secret': job.id_secret,
        })


@login_required
@require_GET
def gensol_status_view(request, problem):
    problem_obj = get_object_or_404(Problem, code=problem)
    if not (request.user.is_superuser or problem_obj.is_editable_by(request.user)):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    job = GensolJob.objects.filter(problem=problem_obj).order_by('-created_date').first()
    if not job:
        return JsonResponse({'job': None})

    return JsonResponse({
        'job': {
            'id': job.id,
            'id_secret': job.id_secret,
            'status': job.status,
            'current_step': job.current_step,
            'current_testcase': job.current_testcase,
            'num_cases': job.num_cases,
            'error_message': job.error_message,
            'error_testcase': job.error_testcase,
            'created_date': job.created_date.isoformat(),
        },
    })
