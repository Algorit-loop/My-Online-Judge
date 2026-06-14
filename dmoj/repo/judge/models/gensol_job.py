import hashlib
import hmac

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from judge.models.problem import Problem
from judge.models.profile import Profile
from judge.models.runtime import Language
from judge.utils.unicode import utf8bytes

__all__ = ['GensolJob']

GENSOL_STATUS_CHOICES = [
    ('PENDING', _('Pending')),
    ('GENERATING_INPUT', _('Generating Input')),
    ('GENERATING_OUTPUT', _('Generating Output')),
    ('UPLOADING', _('Uploading')),
    ('DONE', _('Done')),
    ('ERROR', _('Error')),
]

GENSOL_IN_PROGRESS_STATUSES = ('PENDING', 'GENERATING_INPUT', 'GENERATING_OUTPUT', 'UPLOADING')


class GensolJob(models.Model):
    problem = models.ForeignKey(Problem, verbose_name=_('problem'), on_delete=models.CASCADE)
    user = models.ForeignKey(Profile, verbose_name=_('user'), on_delete=models.CASCADE)
    status = models.CharField(verbose_name=_('status'), max_length=20,
                              choices=GENSOL_STATUS_CHOICES, default='PENDING')
    generator_source = models.TextField(verbose_name=_('generator source'), max_length=65536)
    generator_language = models.ForeignKey(Language, verbose_name=_('generator language'),
                                           related_name='+', on_delete=models.CASCADE)
    solution_source = models.TextField(verbose_name=_('solution source'), max_length=65536)
    solution_language = models.ForeignKey(Language, verbose_name=_('solution language'),
                                          related_name='+', on_delete=models.CASCADE)
    num_cases = models.IntegerField(verbose_name=_('number of test cases'))
    current_step = models.CharField(verbose_name=_('current step'), max_length=20, default='generator')
    current_testcase = models.IntegerField(verbose_name=_('current test case'), default=0)
    error_message = models.TextField(verbose_name=_('error message'), blank=True, default='')
    error_testcase = models.IntegerField(verbose_name=_('error test case'), null=True, blank=True)
    created_date = models.DateTimeField(verbose_name=_('created date'), auto_now_add=True)
    updated_date = models.DateTimeField(verbose_name=_('updated date'), auto_now=True)
    judged_on = models.ForeignKey('Judge', verbose_name=_('judged on'), null=True, blank=True,
                                  on_delete=models.SET_NULL)

    @classmethod
    def get_id_secret(cls, job_id):
        return (hmac.new(utf8bytes(settings.EVENT_DAEMON_GENSOL_KEY), b'%d' % job_id, hashlib.sha512)
                    .hexdigest()[:16] + '%08x' % job_id)

    @cached_property
    def id_secret(self):
        return self.get_id_secret(self.id)

    class Meta:
        verbose_name = _('gensol job')
        verbose_name_plural = _('gensol jobs')
        ordering = ['-created_date']
