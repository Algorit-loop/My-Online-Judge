from operator import itemgetter

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy as _

from judge.models.gensol_submission import GenSolSubmission

_STATUS_COLOR = {
    'AC': '#00a900',
    'WA': '#c00',
    'TLE': '#d58000',
    'MLE': '#d58000',
    'OLE': '#d58000',
    'RTE': '#a000a0',
    'IR': '#a000a0',
    'SC': '#888',
}


class GenSolSubmissionStatusFilter(admin.SimpleListFilter):
    parameter_name = title = 'status'
    __lookups = (('None', _('None')), ('NotDone', _('Not done')), ('EX', _('Exceptional'))) + GenSolSubmission.STATUS
    __handles = set(map(itemgetter(0), GenSolSubmission.STATUS))

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


class GenSolSubmissionAdmin(admin.ModelAdmin):
    readonly_fields = ('user', 'problem', 'date', 'judged_date', 'type', 'job',
                       'source_code', 'error_display', 'case_statuses_table')
    fields = ('type', 'job', 'user', 'problem', 'date', 'judged_date', 'time', 'memory',
              'language', 'status', 'result', 'case_points', 'case_total', 'judged_on',
              'error_display', 'source_code', 'case_statuses_table')
    list_display = ('id', 'type', 'problem_code', 'user_column', 'execution_time',
                    'pretty_memory', 'language_column', 'status', 'result', 'date')
    list_filter = ('type', 'language', GenSolSubmissionStatusFilter)
    search_fields = ('problem__code', 'problem__name', 'user__user__username')
    list_per_page = 50

    def get_queryset(self, request):
        return GenSolSubmission.objects.select_related('problem', 'user__user', 'language').only(
            'problem__code', 'user__user__username', 'language__name',
            'type', 'time', 'memory', 'status', 'result', 'date',
        )

    def has_add_permission(self, request):
        return False

    @admin.display(description=_('problem'), ordering='problem__code')
    def problem_code(self, obj):
        return obj.problem.code

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
        return gettext('%.2f MB') % (memory / 1024)

    @admin.display(description=_('language'), ordering='language__name')
    def language_column(self, obj):
        return obj.language.name

    @admin.display(description=_('compile errors'))
    def error_display(self, obj):
        if not obj.error:
            return gettext('None')
        from django.utils.html import escape
        return format_html(
            '<pre style="font-family:monospace;font-size:13px;background:#1e1e1e;color:#d4d4d4;'
            'border:1px solid #444;padding:10px;overflow:auto;max-height:400px;'
            'white-space:pre-wrap;word-break:break-all;">{}</pre>',
            obj.error,
        )

    @admin.display(description=_('source code'))
    def source_code(self, obj):
        return format_html(
            '<pre style="font-family:monospace;font-size:13px;background:#f8f8f8;border:1px solid #ddd;'
            'padding:10px;overflow:auto;max-height:400px;white-space:pre-wrap;word-break:break-all;">'
            '{}</pre>',
            obj.source,
        )

    @admin.display(description=_('test case statuses'))
    def case_statuses_table(self, obj):
        cases = obj.case_statuses
        if not cases:
            return gettext('No test cases.')

        rows = []
        for tc in cases:
            status = tc.get('status', '?')
            color = _STATUS_COLOR.get(status, '#333')
            time_val = tc.get('time')
            time_str = ('%.3fs' % time_val) if time_val is not None else '-'
            mem = tc.get('memory')
            mem_str = ('%d KB' % mem) if mem is not None and mem < 1000 else (
                '%.2f MB' % (mem / 1024) if mem is not None else '-')
            rows.append(format_html(
                '<tr>'
                '<td style="text-align:center;padding:4px 8px;">{}</td>'
                '<td style="text-align:center;padding:4px 8px;font-weight:bold;color:{};">{}</td>'
                '<td style="text-align:center;padding:4px 8px;">{}</td>'
                '<td style="text-align:center;padding:4px 8px;">{}</td>'
                '</tr>',
                tc.get('case', '?'), color, status, time_str, mem_str,
            ))

        from django.utils.html import format_html_join
        return format_html(
            '<table style="border-collapse:collapse;width:100%;font-size:13px;">'
            '<thead><tr style="background:#f0f0f0;">'
            '<th style="padding:6px 8px;border-bottom:2px solid #ccc;">Case</th>'
            '<th style="padding:6px 8px;border-bottom:2px solid #ccc;">Status</th>'
            '<th style="padding:6px 8px;border-bottom:2px solid #ccc;">Time</th>'
            '<th style="padding:6px 8px;border-bottom:2px solid #ccc;">Memory</th>'
            '</tr></thead>'
            '<tbody style="border:1px solid #ddd;">{}</tbody>'
            '</table>',
            format_html_join('', '{}', ((r,) for r in rows)),
        )
