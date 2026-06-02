from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from judge.models.generate_testcase import GenerateTestcaseJob


class GenerateTestcaseJobAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'problem_link', 'user', 'status_colored',
        'ai_provider', 'ai_model', 'num_cases',
        'result_testcases', 'result_zip_size',
        'created_at', 'completed_at',
    )
    list_filter = ('status', 'ai_provider')
    search_fields = ('problem__code', 'problem__name', 'user__user__username')
    readonly_fields = (
        'id', 'id_secret', 'problem', 'user',
        'ai_provider', 'ai_model', 'num_cases',
        'generator_language', 'solution_language',
        'status', 'error_stage', 'error_log',
        'result_testcases', 'result_zip_size',
        'created_at', 'completed_at',
        'generator_code', 'solution_code',
    )
    ordering = ('-created_at',)
    list_per_page = 50

    fieldsets = (
        (None, {
            'fields': ('id', 'id_secret', 'problem', 'user', 'created_at', 'completed_at'),
        }),
        (_('Configuration'), {
            'fields': ('ai_provider', 'ai_model', 'num_cases', 'generator_language', 'solution_language'),
        }),
        (_('Status'), {
            'fields': ('status', 'error_stage', 'error_log', 'result_testcases', 'result_zip_size'),
        }),
        (_('Code'), {
            'classes': ('collapse',),
            'fields': ('generator_code', 'solution_code'),
        }),
    )

    def problem_link(self, obj):
        return format_html('<a href="/problem/{0}/test_data">{0}</a>', obj.problem.code)
    problem_link.short_description = _('Problem')
    problem_link.admin_order_field = 'problem__code'

    def status_colored(self, obj):
        colors = {
            'DR': '#ff8f00',
            'QU': '#757575',
            'CG': '#1565c0',
            'RG': '#1565c0',
            'CS': '#1565c0',
            'RS': '#1565c0',
            'ZP': '#1565c0',
            'IM': '#1565c0',
            'DN': '#2e7d32',
            'ER': '#c62828',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color, obj.get_status_display(),
        )
    status_colored.short_description = _('Status')
    status_colored.admin_order_field = 'status'

    def has_add_permission(self, request):
        return False
