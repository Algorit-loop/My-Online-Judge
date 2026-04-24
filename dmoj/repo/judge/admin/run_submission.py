from operator import itemgetter

from django.contrib import admin
from django.utils.translation import gettext, gettext_lazy as _

from judge.models.run_submission import RunSubmission


class RunSubmissionStatusFilter(admin.SimpleListFilter):
    parameter_name = title = 'status'
    __lookups = (('None', _('None')), ('NotDone', _('Not done')), ('EX', _('Exceptional'))) + RunSubmission.STATUS
    __handles = set(map(itemgetter(0), RunSubmission.STATUS))

    def lookups(self, request, model_admin):
        return self.__lookups

    def queryset(self, request, queryset):
        if self.value() == 'None':
            return queryset.filter(status=None)
        elif self.value() == 'NotDone':
            return queryset.exclude(status__in=['D', 'IE', 'CE', 'AB'])
        elif self.value() == 'EX':
            return queryset.exclude(status__in=['D', 'CE', 'G', 'AB'])
        elif self.value() in self.__handles:
            return queryset.filter(status=self.value())


class RunSubmissionResultFilter(admin.SimpleListFilter):
    parameter_name = title = 'result'
    __lookups = (('None', _('None')), ('BAD', _('Unaccepted'))) + RunSubmission.RESULT
    __handles = set(map(itemgetter(0), RunSubmission.RESULT))

    def lookups(self, request, model_admin):
        return self.__lookups

    def queryset(self, request, queryset):
        if self.value() == 'None':
            return queryset.filter(result=None)
        elif self.value() == 'BAD':
            return queryset.exclude(result='AC')
        elif self.value() in self.__handles:
            return queryset.filter(result=self.value())


class RunSubmissionAdmin(admin.ModelAdmin):
    readonly_fields = ('user', 'problem', 'date', 'judged_date', 'source', 'case_results')
    fields = ('user', 'problem', 'date', 'judged_date', 'time', 'memory', 'points', 'language',
              'status', 'result', 'case_points', 'case_total', 'judged_on', 'error', 'source', 'case_results')
    list_display = ('id', 'problem_code', 'problem_name', 'user_column', 'execution_time', 'pretty_memory',
                    'points', 'language_column', 'status', 'result', 'date')
    list_filter = ('language', RunSubmissionStatusFilter, RunSubmissionResultFilter)
    search_fields = ('problem__code', 'problem__name', 'user__user__username')
    actions_on_top = True
    actions_on_bottom = True
    date_hierarchy = 'date'
    list_per_page = 50

    def get_queryset(self, request):
        return RunSubmission.objects.select_related('problem', 'user__user', 'language').only(
            'problem__code', 'problem__name', 'user__user__username', 'language__name',
            'time', 'memory', 'points', 'status', 'result', 'date',
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('judge.edit_own_problem')

    @admin.display(description=_('problem code'), ordering='problem__code')
    def problem_code(self, obj):
        return obj.problem.code

    @admin.display(description=_('problem name'), ordering='problem__name')
    def problem_name(self, obj):
        return obj.problem.name

    @admin.display(description=_('user'), ordering='user__user__username')
    def user_column(self, obj):
        return obj.user.user.username

    @admin.display(description=_('time'), ordering='time')
    def execution_time(self, obj):
        return round(obj.time, 2) if obj.time is not None else 'None'

    @admin.display(description=_('memory'), ordering='memory')
    def pretty_memory(self, obj):
        memory = obj.memory
        if memory is None:
            return gettext('None')
        if memory < 1000:
            return gettext('%d KB') % memory
        else:
            return gettext('%.2f MB') % (memory / 1024)

    @admin.display(description=_('language'), ordering='language__name')
    def language_column(self, obj):
        return obj.language.name
