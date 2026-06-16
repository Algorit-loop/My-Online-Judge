from django.db import models
from django.utils.translation import gettext_lazy as _

from judge.models.problem import ProblemType
from judge.models.profile import Profile
from judge.models.submission import Submission

__all__ = ['UserProblemTag']


class UserProblemTag(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='problem_tags',
                             verbose_name=_('user'))
    problem = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='user_tags',
                                verbose_name=_('problem'))
    tag = models.ForeignKey(ProblemType, on_delete=models.CASCADE, related_name='user_problem_tags',
                            verbose_name=_('tag'))
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE,
                                   related_name='user_tags', verbose_name=_('source submission'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    class Meta:
        verbose_name = _('user problem tag')
        verbose_name_plural = _('user problem tags')
        unique_together = ('user', 'submission', 'tag')
        indexes = [
            models.Index(fields=['user', 'tag']),
        ]

    def __str__(self):
        return f'{self.user} - {self.problem} - {self.tag}'
