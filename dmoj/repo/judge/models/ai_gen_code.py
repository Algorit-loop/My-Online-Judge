from django.db import models
from django.utils.translation import gettext_lazy as _

from judge.models.problem import Problem
from judge.models.profile import Profile

__all__ = ['AIGenCode']


class AIGenCode(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='ai_gen_codes',
                                verbose_name=_('problem'))
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='ai_gen_codes',
                             verbose_name=_('user'))
    provider = models.CharField(max_length=20, verbose_name=_('provider'))
    model = models.CharField(max_length=100, verbose_name=_('model'))
    num_cases = models.IntegerField(verbose_name=_('number of test cases'))
    generated_code = models.TextField(verbose_name=_('generated code'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    class Meta:
        verbose_name = _('AI generated code')
        verbose_name_plural = _('AI generated codes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['problem', '-created_at']),
        ]

    def __str__(self):
        return f'GenCode #{self.id} for {self.problem.code} by {self.user}'
