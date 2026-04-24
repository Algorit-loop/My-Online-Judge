from django.db import models
from django.utils.translation import gettext_lazy as _

from judge.models.problem import Problem
from judge.models.profile import Profile
from judge.models.runtime import Language
from judge.models.submission import SUBMISSION_RESULT, SUBMISSION_STATUS

__all__ = ['RunSubmission']


class RunSubmission(models.Model):
    STATUS = SUBMISSION_STATUS
    RESULT = SUBMISSION_RESULT
    IN_PROGRESS_GRADING_STATUS = ('QU', 'P', 'G')

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
    case_results = models.JSONField(verbose_name=_('test case results'), default=list, blank=True)

    class Meta:
        verbose_name = _('run submission')
        verbose_name_plural = _('run submissions')
