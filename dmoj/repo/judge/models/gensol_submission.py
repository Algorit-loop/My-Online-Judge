import hashlib
import hmac
import os

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from judge.models.problem import Problem
from judge.models.profile import Profile
from judge.models.runtime import Language
from judge.models.submission import SUBMISSION_RESULT, SUBMISSION_STATUS
from judge.utils.unicode import utf8bytes

__all__ = ['GenSolSubmission']

GENSOL_TYPE_CHOICES = (
    ('GEN', _('Generator')),
    ('SOL', _('Solution')),
)

# Directory under MEDIA_ROOT or project root to store outputs
GENSOL_OUTPUT_DIR = 'generate_testcase'


class GenSolSubmission(models.Model):
    STATUS = SUBMISSION_STATUS
    RESULT = SUBMISSION_RESULT
    IN_PROGRESS_GRADING_STATUS = ('QU', 'P', 'G')

    type = models.CharField(verbose_name=_('type'), max_length=3, choices=GENSOL_TYPE_CHOICES)
    job = models.ForeignKey('GenerateTestcaseJob', verbose_name=_('job'), on_delete=models.CASCADE,
                            related_name='gensol_submissions', null=True, blank=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    date = models.DateTimeField(verbose_name=_('submission time'), auto_now_add=True)
    time = models.FloatField(verbose_name=_('execution time'), null=True)
    memory = models.FloatField(verbose_name=_('memory usage'), null=True)
    points = models.FloatField(verbose_name=_('points granted'), null=True)
    language = models.ForeignKey(Language, verbose_name=_('submission language'), on_delete=models.CASCADE)
    status = models.CharField(verbose_name=_('status'), max_length=2, choices=SUBMISSION_STATUS, default='QU')
    result = models.CharField(verbose_name=_('result'), max_length=3, choices=SUBMISSION_RESULT,
                              default=None, null=True, blank=True)
    error = models.TextField(verbose_name=_('compile errors'), null=True, blank=True)
    current_testcase = models.IntegerField(default=0)
    batch = models.BooleanField(verbose_name=_('batched cases'), default=False)
    case_points = models.FloatField(verbose_name=_('test case points'), default=0)
    case_total = models.FloatField(verbose_name=_('test case total points'), default=0)
    judged_on = models.ForeignKey('Judge', verbose_name=_('judged on'), null=True, blank=True,
                                  on_delete=models.SET_NULL)
    judged_date = models.DateTimeField(verbose_name=_('submission judge time'), default=None, null=True)
    source = models.TextField(verbose_name=_('source code'), max_length=65536)

    # Lightweight case status (no output stored in DB - outputs go to files)
    case_statuses = models.JSONField(verbose_name=_('test case statuses'), default=list, blank=True)

    @classmethod
    def get_id_secret(cls, sub_id):
        return (hmac.new(utf8bytes(settings.EVENT_DAEMON_RUN_KEY), b'gensol_%d' % sub_id, hashlib.sha512)
                    .hexdigest()[:16] + '%08x' % sub_id)

    @cached_property
    def id_secret(self):
        return self.get_id_secret(self.id)

    def get_output_dir(self):
        """Return the directory path for storing output files.
        Uses /problems/ which is shared across site, celery, and bridged containers.
        """
        base = getattr(settings, 'GENSOL_OUTPUT_ROOT',
                        os.path.join(getattr(settings, 'DMOJ_PROBLEM_DATA_ROOT', '/problems/'),
                                     GENSOL_OUTPUT_DIR))
        return os.path.join(base, str(self.id))

    def get_case_output_path(self, case_number):
        """Return the file path for a specific case output."""
        return os.path.join(self.get_output_dir(), 'case_%d.out' % case_number)

    def read_case_output(self, case_number):
        """Read the output for a specific case from file. Returns None if not found."""
        path = self.get_case_output_path(case_number)
        try:
            with open(path, 'r') as f:
                return f.read()
        except (IOError, OSError):
            return None

    def cleanup_output_files(self):
        """Remove the output directory and all files in it."""
        import shutil
        output_dir = self.get_output_dir()
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)

    class Meta:
        verbose_name = _('gensol submission')
        verbose_name_plural = _('gensol submissions')
