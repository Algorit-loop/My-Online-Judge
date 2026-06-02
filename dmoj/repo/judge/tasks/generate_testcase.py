import io
import logging
import os
import resource
import shutil
import subprocess
import zipfile

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from judge import event_poster as event
from judge.models import Problem, ProblemData, ProblemTestCase, problem_data_storage
from judge.models.generate_testcase import GenerateTestcaseJob
from judge.utils.problem_data import ProblemDataCompiler

logger = logging.getLogger('judge.tasks.generate_testcase')

# Judge-server default: output_limit_length = 25165824 (24 MB)
# See judge-server/dmoj/problem.py:326
DEFAULT_OUTPUT_LIMIT = 25165824

COMPILE_TIMEOUT = 30    # seconds — same as judge IPC_TIMEOUT (60s) but compile rarely needs that much
MAX_ZIP_SIZE = 128 * 1024 * 1024     # 128 MB
MAX_CASES = 40


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
    job.error_log = log[:10000]
    job.completed_at = timezone.now()
    job.save(update_fields=['status', 'error_stage', 'error_log', 'completed_at'])
    _post_event(job, {
        'type': 'error',
        'stage': stage,
        'message': message,
        'log': log[:5000],
    })


def _get_output_limit(problem):
    """Get the output limit for this problem, matching judge-server behaviour.

    Priority: ProblemData.output_limit > judge-server default (24 MB).
    """
    try:
        data = ProblemData.objects.get(problem=problem)
        if data.output_limit is not None:
            return data.output_limit
    except ProblemData.DoesNotExist:
        pass
    return DEFAULT_OUTPUT_LIMIT


@shared_task(bind=True)
def run_generate_testcase(self, job_id):
    try:
        job = GenerateTestcaseJob.objects.get(id=job_id)
    except GenerateTestcaseJob.DoesNotExist:
        logger.error('Job %s not found', job_id)
        return

    problem = job.problem

    # ── Limits: taken directly from the problem, same as a normal submission ──
    time_limit = problem.time_limit          # float, seconds
    memory_limit_kb = problem.memory_limit   # int, kilobytes
    memory_limit_bytes = memory_limit_kb * 1024
    output_limit = _get_output_limit(problem)  # int, bytes

    base_dir = os.path.join(
        getattr(settings, 'DMOJ_PROBLEM_DATA_ROOT', '/problems/'),
        'generate_testcase', 'job_%d' % job.id,
    )
    inputs_dir = os.path.join(base_dir, 'inputs')
    outputs_dir = os.path.join(base_dir, 'outputs')

    try:
        os.makedirs(inputs_dir, exist_ok=True)
        os.makedirs(outputs_dir, exist_ok=True)

        # ── Step 1: Compile generator ──
        _update_status(job, 'CG', {'type': 'compile-generator', 'message': 'Compiling generator...'})

        gen_src = os.path.join(base_dir, 'generator.cpp')
        gen_bin = os.path.join(base_dir, 'generator')
        with open(gen_src, 'w') as f:
            f.write(job.generator_code)

        result = subprocess.run(
            ['g++', '-std=c++17', '-O2', '-o', gen_bin, gen_src],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT,
        )
        if result.returncode != 0:
            _fail(job, 'compile-generator', 'Generator compile error', result.stderr)
            return

        # ── Step 2: Run generator ──
        # Generator creates ALL input files in one run, so it needs more time.
        # Use time_limit × num_cases as a generous budget.
        gen_timeout = max(30.0, time_limit * job.num_cases)
        _update_status(job, 'RG', {
            'type': 'run-generator',
            'message': 'Running generator (timeout %.0fs)...' % gen_timeout,
        })

        def _set_gen_limits():
            """preexec_fn: enforce memory limit on generator, same as solution."""
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))

        try:
            result = subprocess.run(
                [gen_bin],
                capture_output=True, text=True,
                cwd=base_dir,
                timeout=gen_timeout,
                preexec_fn=_set_gen_limits,
            )
        except subprocess.TimeoutExpired:
            _fail(job, 'run-generator', 'Generator TLE (timeout %.0fs)' % gen_timeout)
            return

        if result.returncode != 0:
            _fail(job, 'run-generator', 'Generator runtime error (exit %d)' % result.returncode,
                  result.stderr)
            return

        # ── Step 3: Validate inputs ──
        inp_files = sorted([
            f for f in os.listdir(inputs_dir)
            if f.endswith('.inp') and os.sep not in f and not f.startswith('.')
        ])
        if not inp_files:
            _fail(job, 'run-generator', 'Generator produced no .inp files in inputs/')
            return
        if len(inp_files) > MAX_CASES:
            _fail(job, 'run-generator',
                  'Too many input files: %d (max %d)' % (len(inp_files), MAX_CASES))
            return

        _post_event(job, {
            'type': 'run-generator',
            'message': 'Generated %d input files' % len(inp_files),
            'progress': 100,
        })

        # ── Step 4: Compile solution ──
        _update_status(job, 'CS', {'type': 'compile-solution', 'message': 'Compiling solution...'})

        sol_src = os.path.join(base_dir, 'solution.cpp')
        sol_bin = os.path.join(base_dir, 'solution')
        with open(sol_src, 'w') as f:
            f.write(job.solution_code)

        result = subprocess.run(
            ['g++', '-std=c++17', '-O2', '-o', sol_bin, sol_src],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT,
        )
        if result.returncode != 0:
            _fail(job, 'compile-solution', 'Solution compile error', result.stderr)
            return

        # ── Step 5: Run solution on each input ──
        # Same limits as a normal submission:
        #   time_limit  → from problem
        #   memory_limit → from problem (KB → bytes for RLIMIT_AS)
        #   output_limit → from problem data or default 24 MB
        _update_status(job, 'RS', {
            'type': 'run-solution',
            'message': 'Running solution (TL=%.1fs, ML=%dKB)...' % (time_limit, memory_limit_kb),
            'current': 0,
            'total': len(inp_files),
        })

        def _set_limits():
            """preexec_fn: enforce memory limit via RLIMIT_AS, same as judge sandbox."""
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))

        for i, inp_name in enumerate(inp_files):
            inp_path = os.path.join(inputs_dir, inp_name)
            out_name = inp_name.replace('.inp', '.out')
            out_path = os.path.join(outputs_dir, out_name)

            try:
                with open(inp_path, 'rb') as fin:
                    result = subprocess.run(
                        [sol_bin],
                        stdin=fin, capture_output=True,
                        timeout=time_limit,
                        preexec_fn=_set_limits,
                    )
            except subprocess.TimeoutExpired:
                _fail(job, 'run-solution',
                      'Solution TLE on %s (time limit %.1fs)' % (inp_name, time_limit))
                return

            if result.returncode != 0:
                stderr_text = result.stderr.decode('utf-8', errors='replace')[:3000]
                _fail(job, 'run-solution',
                      'Solution RTE on %s (exit %d, ML=%dKB)' % (
                          inp_name, result.returncode, memory_limit_kb),
                      stderr_text)
                return

            output = result.stdout
            if len(output) > output_limit:
                _fail(job, 'run-solution',
                      'Solution OLE on %s (%s > %s)' % (
                          inp_name, _human_size(len(output)), _human_size(output_limit)))
                return

            with open(out_path, 'wb') as fout:
                fout.write(output)

            _post_event(job, {
                'type': 'run-solution',
                'message': 'Running solution...',
                'current': i + 1,
                'total': len(inp_files),
            })

        # ── Step 6: Package into Themis-format zip ──
        _update_status(job, 'ZP', {'type': 'zipping', 'message': 'Creating testcase zip...'})

        zip_buffer = io.BytesIO()
        problem_code = problem.code

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, inp_name in enumerate(inp_files):
                tc_dir = 'Testcase%03d' % (idx + 1)
                inp_path = os.path.join(inputs_dir, inp_name)
                out_name = inp_name.replace('.inp', '.out')
                out_path = os.path.join(outputs_dir, out_name)

                zf.write(inp_path, os.path.join(problem_code, tc_dir, problem_code + '.inp'))
                zf.write(out_path, os.path.join(problem_code, tc_dir, problem_code + '.out'))

        zip_size = zip_buffer.tell()
        if zip_size > MAX_ZIP_SIZE:
            _fail(job, 'zipping',
                  'Zip too large: %s (max %s)' % (_human_size(zip_size), _human_size(MAX_ZIP_SIZE)))
            return

        zip_buffer.seek(0)

        # ── Step 7: Import into problem ──
        _update_status(job, 'IM', {'type': 'importing', 'message': 'Importing testcases into problem...'})

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

        for idx, inp_name in enumerate(inp_files):
            tc_dir = 'Testcase%03d' % (idx + 1)
            ProblemTestCase.objects.create(
                dataset=problem,
                order=idx + 1,
                type='C',
                input_file=os.path.join(problem_code, tc_dir, problem_code + '.inp'),
                output_file=os.path.join(problem_code, tc_dir, problem_code + '.out'),
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
        job.result_testcases = len(inp_files)
        job.result_zip_size = _human_size(zip_size)
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'result_testcases', 'result_zip_size', 'completed_at'])

        _post_event(job, {
            'type': 'done',
            'message': 'Done!',
            'testcases': len(inp_files),
            'zip_size': _human_size(zip_size),
        })

    except Exception as e:
        logger.exception('Unhandled error in generate_testcase job %s', job_id)
        _fail(job, 'internal', 'Internal error: %s' % str(e))

    finally:
        try:
            if os.path.exists(base_dir):
                shutil.rmtree(base_dir)
        except Exception:
            logger.warning('Failed to clean up %s', base_dir, exc_info=True)


def _human_size(size_bytes):
    if size_bytes < 1024:
        return '%dB' % size_bytes
    elif size_bytes < 1024 * 1024:
        return '%.1fKB' % (size_bytes / 1024)
    else:
        return '%.1fMB' % (size_bytes / (1024 * 1024))
