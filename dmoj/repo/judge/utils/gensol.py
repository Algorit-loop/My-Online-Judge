import io
import logging
import os
import shutil
import zipfile

from django.conf import settings
from django.core.files.base import ContentFile

from judge import event_poster as event
from judge.models.gensol_job import GensolJob, GENSOL_IN_PROGRESS_STATUSES

logger = logging.getLogger('judge.gensol')


def _get_working_dir(job_id):
    return os.path.join(settings.GENSOL_WORKING_DIR, str(job_id))


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _post_event(job_id, data):
    event.post('gensol_%s' % GensolJob.get_id_secret(job_id), data)


def _cleanup_working_dir(job_id):
    working_dir = _get_working_dir(job_id)
    try:
        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
    except OSError:
        logger.warning('Failed to cleanup gensol working dir: %s', working_dir)


def save_testcase_output(job_id, step, position, output):
    """Save output from judge to working directory."""
    working_dir = _get_working_dir(job_id)
    if step == 'generator':
        out_dir = os.path.join(working_dir, 'inputs')
    else:
        out_dir = os.path.join(working_dir, 'outputs')
    _ensure_dir(out_dir)

    filepath = os.path.join(out_dir, '%d.txt' % position)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(output)


def on_gensol_error(job_id, position, status_code, feedback=''):
    """Handle a fatal error on a test case."""
    step = GensolJob.objects.filter(id=job_id).values_list('current_step', flat=True).first() or 'unknown'
    error_msg = '%s failed on testcase %d: %s' % (
        'Generator' if step == 'generator' else 'Solution',
        position, status_code,
    )
    if feedback:
        error_msg += ' (%s)' % feedback[:500]

    GensolJob.objects.filter(id=job_id).update(
        status='ERROR',
        error_message=error_msg,
        error_testcase=position,
    )
    _post_event(job_id, {
        'type': 'error',
        'message': error_msg,
        'testcase': position,
    })
    _cleanup_working_dir(job_id)
    logger.info('Gensol job %d failed: %s', job_id, error_msg)


def on_gensol_grading_end(job_id, gensol_step):
    """Handle grading end — transition to next step or finalize."""
    try:
        job = GensolJob.objects.get(id=job_id)
    except GensolJob.DoesNotExist:
        logger.error('GensolJob %d not found in grading end', job_id)
        return

    # If job is already in ERROR state (from on_gensol_error), skip
    if job.status == 'ERROR':
        logger.info('Gensol job %d already in error state, skipping grading end', job_id)
        return

    if gensol_step == 'generator':
        _transition_to_solution(job)
    elif gensol_step == 'solution':
        _finalize_job(job)


def _transition_to_solution(job):
    """Generator done. Build zip from inputs + empty outputs, dispatch solution."""
    logger.info('Gensol job %d: generator done, transitioning to solution', job.id)

    try:
        working_dir = _get_working_dir(job.id)
        problem = job.problem

        # Build zip from generated inputs + empty outputs
        zip_buffer = _build_zip(problem.code, job.num_cases, working_dir, include_outputs=False)

        # Upload zip and regenerate init.yml
        _upload_zip_and_compile(problem, zip_buffer, job.num_cases)

        # Update job state
        GensolJob.objects.filter(id=job.id).update(
            status='GENERATING_OUTPUT',
            current_step='solution',
            current_testcase=0,
        )

        _post_event(job.id, {'type': 'step-change', 'step': 'solution'})

        # Dispatch solution to judge
        _dispatch_gensol(job, 'solution')

    except Exception as e:
        logger.exception('Error transitioning gensol job %d to solution', job.id)
        GensolJob.objects.filter(id=job.id).update(
            status='ERROR', error_message='Failed to prepare solution step: %s' % str(e)[:500])
        _post_event(job.id, {'type': 'error', 'message': str(e)[:500]})
        _cleanup_working_dir(job.id)


def _finalize_job(job):
    """Solution done. Build final zip, validate size, upload."""
    logger.info('Gensol job %d: solution done, finalizing', job.id)

    try:
        working_dir = _get_working_dir(job.id)
        problem = job.problem

        # Build final zip with inputs + outputs
        zip_buffer = _build_zip(problem.code, job.num_cases, working_dir, include_outputs=True)

        # Check zip size
        max_size = getattr(settings, 'GENSOL_MAX_ZIP_SIZE', 64 * 1024 * 1024)
        if zip_buffer.tell() > max_size:
            error_msg = 'Generated zip is too large: %.1f MB (max %.1f MB)' % (
                zip_buffer.tell() / 1024 / 1024, max_size / 1024 / 1024)
            GensolJob.objects.filter(id=job.id).update(status='ERROR', error_message=error_msg)
            _post_event(job.id, {'type': 'error', 'message': error_msg})
            _cleanup_working_dir(job.id)
            return

        # Upload final zip and regenerate init.yml
        _upload_zip_and_compile(problem, zip_buffer, job.num_cases)

        # Mark done
        GensolJob.objects.filter(id=job.id).update(status='DONE')
        _post_event(job.id, {'type': 'done'})

        # Cleanup working directory
        try:
            shutil.rmtree(working_dir)
        except OSError:
            logger.warning('Failed to cleanup gensol working dir: %s', working_dir)

        logger.info('Gensol job %d completed successfully', job.id)

    except Exception as e:
        logger.exception('Error finalizing gensol job %d', job.id)
        GensolJob.objects.filter(id=job.id).update(
            status='ERROR', error_message='Failed to finalize: %s' % str(e)[:500])
        _post_event(job.id, {'type': 'error', 'message': str(e)[:500]})
        _cleanup_working_dir(job.id)


def start_gensol_job(job):
    """Step 1: Create virtual testcases and dispatch generator to judge."""
    problem = job.problem
    num_cases = job.num_cases
    working_dir = _get_working_dir(job.id)
    _ensure_dir(working_dir)
    _ensure_dir(os.path.join(working_dir, 'inputs'))
    _ensure_dir(os.path.join(working_dir, 'outputs'))

    try:
        # Delete existing testcases
        from judge.models.problem_data import ProblemTestCase, ProblemData
        ProblemTestCase.objects.filter(dataset=problem).delete()

        # Create virtual zip: each input file contains its index number
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i in range(1, num_cases + 1):
                folder = '%s/Testcase%03d' % (problem.code, i)
                zf.writestr('%s/%s.inp' % (folder, problem.code), str(i))
                zf.writestr('%s/%s.out' % (folder, problem.code), '')
        zip_buffer.seek(0)

        # Upload zip
        _upload_zip_and_compile(problem, zip_buffer, num_cases)

        # Update job state
        GensolJob.objects.filter(id=job.id).update(
            status='GENERATING_INPUT',
            current_step='generator',
            current_testcase=0,
        )

        _post_event(job.id, {'type': 'step-change', 'step': 'generator'})

        # Dispatch generator to judge
        _dispatch_gensol(job, 'generator')

    except Exception as e:
        logger.exception('Error starting gensol job %d', job.id)
        GensolJob.objects.filter(id=job.id).update(
            status='ERROR', error_message='Failed to start: %s' % str(e)[:500])
        _post_event(job.id, {'type': 'error', 'message': str(e)[:500]})
        _cleanup_working_dir(job.id)


def _build_zip(problem_code, num_cases, working_dir, include_outputs=False):
    """Build a zip file from files in the working directory."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i in range(1, num_cases + 1):
            folder = '%s/Testcase%03d' % (problem_code, i)

            # Input file
            input_path = os.path.join(working_dir, 'inputs', '%d.txt' % i)
            if os.path.exists(input_path):
                with open(input_path, 'r', encoding='utf-8') as f:
                    input_data = f.read()
            else:
                input_data = str(i)
            zf.writestr('%s/%s.inp' % (folder, problem_code), input_data)

            # Output file
            if include_outputs:
                output_path = os.path.join(working_dir, 'outputs', '%d.txt' % i)
                if os.path.exists(output_path):
                    with open(output_path, 'r', encoding='utf-8') as f:
                        output_data = f.read()
                else:
                    output_data = ''
            else:
                output_data = ''
            zf.writestr('%s/%s.out' % (folder, problem_code), output_data)

    zip_buffer.seek(0)
    return zip_buffer


def _upload_zip_and_compile(problem, zip_buffer, num_cases):
    """Upload zip to problem data storage and regenerate init.yml + ProblemTestCase entries."""
    from judge.models.problem_data import ProblemData, ProblemTestCase, problem_data_storage
    from judge.utils.problem_data import ProblemDataCompiler

    # Get or create ProblemData
    data, _ = ProblemData.objects.get_or_create(problem=problem)

    # Save zip file
    zip_name = '%s/data.zip' % problem.code
    zip_content = ContentFile(zip_buffer.read())
    problem_data_storage.save(zip_name, zip_content)

    # Update ProblemData to reference the zip
    data.zipfile = zip_name
    data.update_zipfile_size()
    if not data.checker:
        data.checker = 'standard'
    data.save()

    # Delete old testcases and create new ones
    ProblemTestCase.objects.filter(dataset=problem).delete()
    cases = []
    for i in range(1, num_cases + 1):
        folder = '%s/Testcase%03d' % (problem.code, i)
        cases.append(ProblemTestCase(
            dataset=problem,
            order=i,
            type='C',
            input_file='%s/%s.inp' % (folder, problem.code),
            output_file='%s/%s.out' % (folder, problem.code),
            points=1,
            is_pretest=False,
            is_sample=False,
        ))
    ProblemTestCase.objects.bulk_create(cases)

    # Get valid files from zip
    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer) as zf:
        valid_files = zf.namelist()

    # Regenerate init.yml
    ProblemDataCompiler.generate(
        problem, data,
        ProblemTestCase.objects.filter(dataset=problem).order_by('order'),
        valid_files,
    )


def _dispatch_gensol(job, step):
    """Send gensol-request to bridge via judgeapi."""
    from judge.judge_priority import DEFAULT_PRIORITY
    from judge.judgeapi import judge_request

    source = job.generator_source if step == 'generator' else job.solution_source
    language = job.generator_language if step == 'generator' else job.solution_language

    result = judge_request({
        'name': 'gensol-request',
        'submission-id': job.id,
        'problem-id': job.problem.code,
        'language': language.key,
        'source': source,
        'judge-id': None,
        'banned-judges': [],
        'priority': DEFAULT_PRIORITY,
        'gensol-step': step,
    })

    if result.get('name') != 'gensol-received' or result.get('submission-id') != job.id:
        raise ValueError('Unexpected bridge response: %s' % result)
