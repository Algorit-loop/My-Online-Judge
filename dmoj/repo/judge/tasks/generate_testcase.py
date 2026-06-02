import io
import logging
import time
import zipfile

from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from judge import event_poster as event
from judge.judgeapi import judge_run_submission
from judge.models import ProblemData, ProblemTestCase, problem_data_storage
from judge.models.generate_testcase import GenerateTestcaseJob
from judge.models.run_submission import RunSubmission
from judge.utils.problem_data import ProblemDataCompiler

logger = logging.getLogger('judge.tasks.generate_testcase')

MAX_ZIP_SIZE = 128 * 1024 * 1024     # 128 MB
MAX_CASES = 40
POLL_INTERVAL = 1.0                  # seconds between polls
POLL_TIMEOUT = 300                   # max seconds to wait for a judge run


def _post_event(job, data):
    channel = 'gentc_%s' % job.id_secret
    try:
        event.post(channel, data)
    except Exception:
        logger.warning('Failed to post event for job %s', job.id, exc_info=True)


def _update_status(job, status, event_data=None):
    job.status = status
    job.save(update_fields=['status'])
    if event_data:
        _post_event(job, event_data)


def _fail(job, stage, message, log=''):
    job.status = 'ER'
    job.error_stage = stage
    # Store the detailed log if provided, otherwise store the message itself
    job.error_log = (log or message)[:10000]
    job.completed_at = timezone.now()
    job.save(update_fields=['status', 'error_stage', 'error_log', 'completed_at'])
    _post_event(job, {
        'type': 'error',
        'stage': stage,
        'message': message,
        'log': (log or message)[:5000],
    })


def _wait_for_run(run_sub, timeout=POLL_TIMEOUT):
    """Poll a RunSubmission until it finishes. Returns the refreshed RunSubmission."""
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        time.sleep(POLL_INTERVAL)
        run_sub.refresh_from_db()
        if run_sub.status not in RunSubmission.IN_PROGRESS_GRADING_STATUS:
            return run_sub
    return run_sub


def _dispatch_to_judge(problem, language, source, custom_inputs, user_profile):
    """Create a RunSubmission and dispatch it to the judge via the bridge.

    Returns (run_sub, error_msg). On success error_msg is None.
    """
    run_sub = RunSubmission.objects.create(
        user=user_profile,
        problem=problem,
        language=language,
        source=source,
        status='QU',
    )

    success = judge_run_submission(
        run_sub,
        sample_input_files=[],
        custom_inputs=custom_inputs,
    )
    if not success:
        run_sub.delete()
        return None, 'Failed to dispatch to judge (no judge available or bridge error)'

    return run_sub, None


def _check_run_result(run_sub, stage_label, num_custom_inputs):
    """Check a completed RunSubmission for fatal errors (TLE/MLE/RTE/OLE).

    We only check the *custom input* cases (skip any sample cases the judge
    included). The judge marks custom-input cases as WA because there is no
    expected output, but that is fine — we only need the raw output.

    Returns (case_outputs, error_msg). On success error_msg is None.
    case_outputs is a list of output strings, one per custom input.
    """
    if run_sub.status == 'CE':
        return None, 'Compile error:\n%s' % (run_sub.error or '')
    if run_sub.status == 'IE':
        return None, 'Internal error:\n%s' % (run_sub.error or '')
    if run_sub.status not in ('D',):
        return None, 'Unexpected status: %s' % run_sub.status

    all_results = run_sub.case_results or []

    # The judge may prepend sample test cases before our custom inputs.
    # Custom inputs are always at the tail: last `num_custom_inputs` entries.
    if len(all_results) < num_custom_inputs:
        return None, '%s: expected %d results, got %d' % (
            stage_label, num_custom_inputs, len(all_results))

    custom_results = all_results[len(all_results) - num_custom_inputs:]

    for i, case in enumerate(custom_results):
        status = case.get('status', '')
        if status == 'TLE':
            return None, '%s: Time Limit Exceeded on case %d' % (stage_label, i + 1)
        elif status == 'MLE':
            return None, '%s: Memory Limit Exceeded on case %d' % (stage_label, i + 1)
        elif status == 'OLE':
            return None, '%s: Output Limit Exceeded on case %d' % (stage_label, i + 1)
        elif status == 'RTE':
            return None, '%s: Runtime Error on case %d' % (stage_label, i + 1)
        elif status == 'IR':
            return None, '%s: Invalid Return on case %d' % (stage_label, i + 1)
        # WA and AC are both fine — WA is expected for custom inputs with no expected output

    return custom_results, None


def _human_size(size_bytes):
    if size_bytes < 1024:
        return '%dB' % size_bytes
    elif size_bytes < 1024 * 1024:
        return '%.1fKB' % (size_bytes / 1024)
    else:
        return '%.1fMB' % (size_bytes / (1024 * 1024))


@shared_task(bind=True)
def run_generate_testcase(self, job_id):
    try:
        job = GenerateTestcaseJob.objects.select_related(
            'problem', 'user', 'generator_language', 'solution_language',
        ).get(id=job_id)
    except GenerateTestcaseJob.DoesNotExist:
        logger.error('Job %s not found', job_id)
        return

    problem = job.problem
    num_cases = job.num_cases
    user_profile = job.user

    gen_language = job.generator_language
    sol_language = job.solution_language

    if not gen_language or not sol_language:
        _fail(job, 'internal', 'Generator or solution language not set')
        return

    try:
        # ── Step 1+2: Compile & Run Generator on Judge ──
        # The generator reads a case number (1..N) from stdin and outputs one test input to stdout.
        # We send N custom inputs: ["1", "2", ..., "N"]
        _update_status(job, 'CG', {
            'type': 'compile-generator',
            'message': 'Compiling generator on judge...',
        })

        gen_inputs = [str(i) for i in range(1, num_cases + 1)]

        gen_run, err = _dispatch_to_judge(problem, gen_language, job.generator_code, gen_inputs, user_profile)
        if err:
            _fail(job, 'compile-generator', err)
            return

        _update_status(job, 'RG', {
            'type': 'run-generator',
            'message': 'Running generator (%d cases)...' % num_cases,
        })

        gen_run = _wait_for_run(gen_run)

        # Check if still running (timeout)
        if gen_run.status in RunSubmission.IN_PROGRESS_GRADING_STATUS:
            _fail(job, 'run-generator', 'Generator timed out waiting for judge (%ds)' % POLL_TIMEOUT)
            return

        # Check for compile error specifically
        if gen_run.status == 'CE':
            _fail(job, 'compile-generator', 'Generator compile error', gen_run.error or '')
            return

        gen_results, err = _check_run_result(gen_run, 'Generator', num_cases)
        if err:
            _fail(job, 'run-generator', err)
            return

        if not gen_results:
            _fail(job, 'run-generator', 'Generator produced no output')
            return

        _post_event(job, {
            'type': 'run-generator',
            'message': 'Generated %d input(s)' % len(gen_results),
            'progress': 100,
        })

        # Collect generator outputs as test case inputs
        test_inputs = []
        for i, case in enumerate(gen_results):
            output = case.get('output', '')
            if not output.strip():
                _fail(job, 'run-generator',
                      'Generator produced empty output for case %d' % (i + 1))
                return
            test_inputs.append(output)

        # ── Step 3+4: Compile & Run Solution on Judge ──
        _update_status(job, 'CS', {
            'type': 'compile-solution',
            'message': 'Compiling solution on judge...',
        })

        sol_run, err = _dispatch_to_judge(problem, sol_language, job.solution_code, test_inputs, user_profile)
        if err:
            _fail(job, 'compile-solution', err)
            return

        _update_status(job, 'RS', {
            'type': 'run-solution',
            'message': 'Running solution (%d cases)...' % len(test_inputs),
            'current': 0,
            'total': len(test_inputs),
        })

        sol_run = _wait_for_run(sol_run)

        if sol_run.status in RunSubmission.IN_PROGRESS_GRADING_STATUS:
            _fail(job, 'run-solution', 'Solution timed out waiting for judge (%ds)' % POLL_TIMEOUT)
            return

        if sol_run.status == 'CE':
            _fail(job, 'compile-solution', 'Solution compile error', sol_run.error or '')
            return

        sol_results, err = _check_run_result(sol_run, 'Solution', len(test_inputs))
        if err:
            _fail(job, 'run-solution', err)
            return

        if not sol_results or len(sol_results) != len(test_inputs):
            _fail(job, 'run-solution',
                  'Solution produced %d outputs, expected %d' % (
                      len(sol_results) if sol_results else 0, len(test_inputs)))
            return

        _post_event(job, {
            'type': 'run-solution',
            'message': 'Solution done',
            'current': len(test_inputs),
            'total': len(test_inputs),
        })

        test_outputs = [case.get('output', '') for case in sol_results]

        # ── Step 5: Package into Themis-format zip ──
        _update_status(job, 'ZP', {'type': 'zipping', 'message': 'Creating testcase zip...'})

        zip_buffer = io.BytesIO()
        problem_code = problem.code

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx in range(len(test_inputs)):
                tc_dir = 'Testcase%03d' % (idx + 1)
                inp_path = '%s/%s/%s.inp' % (problem_code, tc_dir, problem_code)
                out_path = '%s/%s/%s.out' % (problem_code, tc_dir, problem_code)
                zf.writestr(inp_path, test_inputs[idx])
                zf.writestr(out_path, test_outputs[idx])

        zip_size = zip_buffer.tell()
        if zip_size > MAX_ZIP_SIZE:
            _fail(job, 'zipping',
                  'Zip too large: %s (max %s)' % (_human_size(zip_size), _human_size(MAX_ZIP_SIZE)))
            return

        zip_buffer.seek(0)

        # ── Step 6: Import into problem (atomic) ──
        _update_status(job, 'IM', {'type': 'importing', 'message': 'Importing testcases into problem...'})

        with transaction.atomic():
            problem_data, _ = ProblemData.objects.get_or_create(problem=problem)

            if problem_data.zipfile:
                try:
                    problem_data_storage.delete(problem_data.zipfile.name)
                except Exception:
                    pass

            zip_filename = '%s/data.zip' % problem_code
            saved_name = problem_data_storage.save(zip_filename, ContentFile(zip_buffer.read()))
            problem_data.zipfile.name = saved_name
            problem_data.save(update_fields=['zipfile'])

            ProblemTestCase.objects.filter(dataset=problem).delete()

            for idx in range(len(test_inputs)):
                tc_dir = 'Testcase%03d' % (idx + 1)
                ProblemTestCase.objects.create(
                    dataset=problem,
                    order=idx + 1,
                    type='C',
                    input_file='%s/%s/%s.inp' % (problem_code, tc_dir, problem_code),
                    output_file='%s/%s/%s.out' % (problem_code, tc_dir, problem_code),
                    points=1,
                    is_pretest=False,
                    is_sample=(idx == 0),
                )

            all_cases = ProblemTestCase.objects.filter(dataset=problem).order_by('order')
            try:
                valid_files = []
                with zipfile.ZipFile(problem_data_storage.path(saved_name), 'r') as zf:
                    valid_files = zf.namelist()
                ProblemDataCompiler.generate(problem, problem_data, all_cases, valid_files)
            except Exception:
                logger.warning('Failed to compile init.yml for %s', problem.code, exc_info=True)

        # ── Done ──
        job.status = 'DN'
        job.result_testcases = len(test_inputs)
        job.result_zip_size = _human_size(zip_size)
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'result_testcases', 'result_zip_size', 'completed_at'])

        _post_event(job, {
            'type': 'done',
            'message': 'Done!',
            'testcases': len(test_inputs),
            'zip_size': _human_size(zip_size),
        })

    except Exception as e:
        logger.exception('Unhandled error in generate_testcase job %s', job_id)
        _fail(job, 'internal', 'Internal error: %s' % str(e))
