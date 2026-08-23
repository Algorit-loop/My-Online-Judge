import logging
import signal
import threading
from functools import partial

from django.conf import settings

from judge.bridge.django_handler import DjangoHandler
from judge.bridge.judge_handler import JudgeHandler
from judge.bridge.judge_list import JudgeList
from judge.bridge.server import Server
from judge.models import Judge, Submission
from judge.models.gensol_job import GENSOL_IN_PROGRESS_STATUSES, GensolJob

logger = logging.getLogger('judge.bridge')

GENSOL_RESTART_MESSAGE = ('Internal error: the judging bridge restarted while this job was running. '
                          'Please start the generation again.')


def reset_judges():
    Judge.objects.update(online=False, ping=None, load=None)


def reset_gensol_jobs():
    """A gensol job is driven entirely from this process's in-memory state (the judge connection and the
    dispatch queue), so anything still marked in-progress when the bridge starts has been orphaned by the
    restart — nothing will ever finish it, and the job would otherwise block the problem forever via the
    'already in progress' check in GensolStartView. Fail them the same way we fail in-progress Submissions
    above, so the teacher just hits Generate again.
    """
    from judge import event_poster as event
    from judge.utils.gensol import _cleanup_working_dir

    stale_ids = list(GensolJob.objects.filter(status__in=GENSOL_IN_PROGRESS_STATUSES)
                     .values_list('id', flat=True))
    if not stale_ids:
        return

    GensolJob.objects.filter(id__in=stale_ids).update(status='ERROR', error_message=GENSOL_RESTART_MESSAGE)
    for job_id in stale_ids:
        _cleanup_working_dir(job_id)
        # Best-effort: lets a page that is still open flip out of its spinner without a reload. The event
        # daemon is a separate container and may not be up yet at bridge startup, so never let this abort
        # the reset — the page's own ERROR restore path covers it after a reload.
        try:
            event.post('gensol_%s' % GensolJob.get_id_secret(job_id),
                       {'type': 'internal-error', 'message': GENSOL_RESTART_MESSAGE})
        except Exception:
            logger.warning('Could not post restart event for orphaned gensol job %d', job_id)

    logger.info('Reset %d orphaned gensol job(s) on bridge startup: %s', len(stale_ids), stale_ids)


def judge_daemon(run_monitor=False, problem_storage_globs=None):
    reset_judges()
    Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS) \
        .update(status='IE', result='IE', error=None)
    reset_gensol_jobs()
    judges = JudgeList()

    monitor = None
    if run_monitor:
        from judge.bridge.monitor import Monitor
        monitor = Monitor(judges, problem_storage_globs or [])

    judge_server = Server(
        settings.BRIDGED_JUDGE_ADDRESS,
        partial(JudgeHandler, judges=judges, ignore_problems_packet=run_monitor),
    )
    django_server = Server(settings.BRIDGED_DJANGO_ADDRESS, partial(DjangoHandler, judges=judges))

    if monitor is not None:
        monitor.start()
    threading.Thread(target=django_server.serve_forever).start()
    threading.Thread(target=judge_server.serve_forever).start()

    stop = threading.Event()

    def signal_handler(signum, _):
        logger.info('Exiting due to %s', signal.Signals(signum).name)
        stop.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        stop.wait()
    finally:
        if monitor is not None:
            monitor.stop()
        django_server.shutdown()
        judge_server.shutdown()
