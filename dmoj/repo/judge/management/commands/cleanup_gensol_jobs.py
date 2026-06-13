from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from judge.models.gensol_job import GensolJob, GENSOL_IN_PROGRESS_STATUSES
from judge.utils.gensol import _cleanup_working_dir


class Command(BaseCommand):
    help = 'Mark stuck gensol jobs as ERROR and clean up their working directories.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes', type=int, default=30,
            help='Jobs in progress longer than this many minutes are considered stuck (default: 30).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Only show what would be cleaned up, without making changes.',
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=options['minutes'])
        stuck_jobs = GensolJob.objects.filter(
            status__in=GENSOL_IN_PROGRESS_STATUSES,
            updated_date__lt=cutoff,
        )

        count = stuck_jobs.count()
        if count == 0:
            self.stdout.write('No stuck gensol jobs found.')
            return

        for job in stuck_jobs:
            self.stdout.write('Stuck job #%d (problem=%s, status=%s, updated=%s)' % (
                job.id, job.problem.code, job.status, job.updated_date))
            if not options['dry_run']:
                _cleanup_working_dir(job.id)

        if not options['dry_run']:
            updated = stuck_jobs.update(
                status='ERROR',
                error_message='Job timed out (stuck for >%d minutes)' % options['minutes'],
            )
            self.stdout.write(self.style.SUCCESS('Cleaned up %d stuck job(s).' % updated))
        else:
            self.stdout.write('Dry run: would clean up %d job(s).' % count)
