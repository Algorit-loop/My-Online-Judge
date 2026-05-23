import re
from operator import itemgetter

from django.contrib import admin
from django.utils.html import escape, format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext, gettext_lazy as _

from judge.models.run_submission import RunSubmission

_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]|\x1b\[[0-9;]*m|\x0f|\x01[^\x02]*\x02')

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
    readonly_fields = ('user', 'problem', 'date', 'judged_date', 'source_code', 'error_display', 'case_results_table')
    fields = ('user', 'problem', 'date', 'judged_date', 'time', 'memory', 'points', 'language',
              'status', 'result', 'case_points', 'case_total', 'judged_on', 'error_display', 'source_code',
              'case_results_table')
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

    @admin.display(description=_('compile errors'))
    def error_display(self, obj):
        if not obj.error:
            return gettext('None')
        try:
            from ansi2html import Ansi2HTMLConverter
            html = Ansi2HTMLConverter(inline=True).convert(obj.error, full=False)
        except Exception:
            html = escape(_ANSI_ESCAPE.sub('', obj.error))
        return mark_safe(
            '<pre style="font-family:monospace;font-size:13px;background:#1e1e1e;color:#d4d4d4;'
            'border:1px solid #444;padding:10px;overflow:auto;max-height:400px;'
            'white-space:pre-wrap;word-break:break-all;">' + html + '</pre>'
        )

    @admin.display(description=_('source code'))
    def source_code(self, obj):
        return format_html(
            '<pre style="font-family:monospace;font-size:13px;background:#f8f8f8;border:1px solid #ddd;'
            'padding:10px;overflow:auto;max-height:400px;white-space:pre-wrap;word-break:break-all;">'
            '{}</pre>',
            obj.source,
        )

    @admin.display(description=_('test case results'))
    def case_results_table(self, obj):
        cases = obj.case_results
        if not cases:
            return gettext('No test cases.')

        def _fmt_memory(mem):
            if mem is None:
                return '—'
            if mem < 1000:
                return '%d KB' % mem
            return '%.2f MB' % (mem / 1024)

        rows_html = []
        for tc in cases:
            status = tc.get('status', '?')
            color = _STATUS_COLOR.get(status, '#333')
            time_val = tc.get('time')
            time_str = ('%.3fs' % time_val) if time_val is not None else '—'
            mem_str = _fmt_memory(tc.get('memory'))
            output = tc.get('output') or ''
            rows_html.append(format_html(
                '<tr>'
                '<td style="text-align:center;padding:4px 8px;">{case}</td>'
                '<td style="text-align:center;padding:4px 8px;font-weight:bold;color:{color};">{status}</td>'
                '<td style="text-align:center;padding:4px 8px;">{time}</td>'
                '<td style="text-align:center;padding:4px 8px;">{memory}</td>'
                '<td style="padding:4px 8px;font-family:monospace;white-space:pre-wrap;word-break:break-all;'
                'max-width:500px;">{output}</td>'
                '</tr>',
                case=tc.get('case', '?'),
                color=color,
                status=status,
                time=time_str,
                memory=mem_str,
                output=output,
            ))

        return format_html(
            '<table style="border-collapse:collapse;width:100%;font-size:13px;">'
            '<thead><tr style="background:#f0f0f0;">'
            '<th style="padding:6px 8px;border-bottom:2px solid #ccc;text-align:center;">{}</th>'
            '<th style="padding:6px 8px;border-bottom:2px solid #ccc;text-align:center;">{}</th>'
            '<th style="padding:6px 8px;border-bottom:2px solid #ccc;text-align:center;">{}</th>'
            '<th style="padding:6px 8px;border-bottom:2px solid #ccc;text-align:center;">{}</th>'
            '<th style="padding:6px 8px;border-bottom:2px solid #ccc;">{}</th>'
            '</tr></thead>'
            '<tbody style="border:1px solid #ddd;">{}</tbody>'
            '</table>',
            _('Case'), _('Status'), _('Time'), _('Memory'), _('Output'),
            format_html_join('', '{}', ((r,) for r in rows_html)),
        )
