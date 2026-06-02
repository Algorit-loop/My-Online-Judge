import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from judge.models.problem import Problem
from judge.models.profile import Profile

__all__ = ['GenerateTestcaseJob']

STATUS_CHOICES = [
    ('DR', _('Draft')),
    ('QU', _('Queued')),
    ('AI', _('AI Generating')),
    ('CG', _('Compiling Generator')),
    ('RG', _('Running Generator')),
    ('CS', _('Compiling Solution')),
    ('RS', _('Running Solution')),
    ('ZP', _('Zipping')),
    ('IM', _('Importing')),
    ('DN', _('Done')),
    ('ER', _('Error')),
]


class GenerateTestcaseJob(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE,
                                related_name='generate_testcase_jobs', verbose_name=_('problem'))
    user = models.ForeignKey(Profile, on_delete=models.CASCADE,
                             related_name='generate_testcase_jobs', verbose_name=_('user'))

    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='QU', verbose_name=_('status'))
    id_secret = models.CharField(max_length=36, unique=True, default=uuid.uuid4, verbose_name=_('id secret'))

    # AI config
    ai_provider = models.CharField(max_length=20, blank=True, verbose_name=_('AI provider'))
    ai_model = models.CharField(max_length=100, blank=True, verbose_name=_('AI model'))

    # Code
    generator_code = models.TextField(blank=True, default='', verbose_name=_('generator code'))
    solution_code = models.TextField(blank=True, default='', verbose_name=_('solution code'))

    num_cases = models.IntegerField(default=20, verbose_name=_('number of test cases'))

    # Result / error
    error_stage = models.CharField(max_length=50, blank=True, default='', verbose_name=_('error stage'))
    error_log = models.TextField(blank=True, default='', verbose_name=_('error log'))
    result_testcases = models.IntegerField(null=True, blank=True, verbose_name=_('result test cases'))
    result_zip_size = models.CharField(max_length=20, blank=True, default='', verbose_name=_('result zip size'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('completed at'))

    class Meta:
        verbose_name = _('generate testcase job')
        verbose_name_plural = _('generate testcase jobs')
        ordering = ['-created_at']

    def __str__(self):
        return f'GenerateTestcaseJob #{self.id} [{self.get_status_display()}] for {self.problem.code}'
