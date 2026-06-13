from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from judge.models.gensol_job import GensolJob


class GensolJobStatusFilter(admin.SimpleListFilter):
    parameter_name = title = 'status'

    def lookups(self, request, model_admin):
        return GensolJob._meta.get_field('status').choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())


class GensolJobAdmin(admin.ModelAdmin):
    readonly_fields = ('problem', 'user', 'created_date', 'updated_date',
                       'generator_source_display', 'solution_source_display')
    list_display = ('id', 'problem_code', 'user_name', 'status', 'current_step',
                    'num_cases', 'current_testcase', 'generator_lang', 'solution_lang', 'created_date')
    list_filter = (GensolJobStatusFilter, 'generator_language', 'solution_language')
    search_fields = ('problem__code', 'problem__name', 'user__user__username')
    date_hierarchy = 'created_date'
    list_per_page = 50

    fieldsets = (
        (None, {
            'fields': ('problem', 'user', 'status', 'current_step', 'num_cases',
                       'current_testcase', 'judged_on'),
        }),
        (_('Generator'), {
            'fields': ('generator_language', 'generator_source_display'),
        }),
        (_('Solution'), {
            'fields': ('solution_language', 'solution_source_display'),
        }),
        (_('Error'), {
            'fields': ('error_message', 'error_testcase'),
            'classes': ('collapse',),
        }),
        (_('Dates'), {
            'fields': ('created_date', 'updated_date'),
        }),
    )

    def get_queryset(self, request):
        return GensolJob.objects.select_related(
            'problem', 'user__user', 'generator_language', 'solution_language', 'judged_on',
        )

    def has_add_permission(self, request):
        return False

    @admin.display(description=_('problem'), ordering='problem__code')
    def problem_code(self, obj):
        return obj.problem.code

    @admin.display(description=_('user'), ordering='user__user__username')
    def user_name(self, obj):
        return obj.user.user.username

    @admin.display(description=_('gen lang'), ordering='generator_language__name')
    def generator_lang(self, obj):
        return obj.generator_language.name

    @admin.display(description=_('sol lang'), ordering='solution_language__name')
    def solution_lang(self, obj):
        return obj.solution_language.name

    @admin.display(description=_('generator source'))
    def generator_source_display(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<pre style="font-family:monospace;font-size:13px;background:#f8f8f8;border:1px solid #ddd;'
            'padding:10px;overflow:auto;max-height:400px;white-space:pre-wrap;word-break:break-all;">'
            '{}</pre>',
            obj.generator_source,
        )

    @admin.display(description=_('solution source'))
    def solution_source_display(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<pre style="font-family:monospace;font-size:13px;background:#f8f8f8;border:1px solid #ddd;'
            'padding:10px;overflow:auto;max-height:400px;white-space:pre-wrap;word-break:break-all;">'
            '{}</pre>',
            obj.solution_source,
        )
