from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from judge.models.ai_gen_code import AIGenCode


class AIGenCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'problem_code', 'user', 'provider', 'model', 'num_cases', 'created_at')
    list_filter = ('provider', 'created_at')
    search_fields = ('problem__code', 'problem__name', 'user__user__username', 'provider', 'model')
    readonly_fields = ('problem', 'user', 'provider', 'model', 'num_cases', 'generated_code', 'created_at')
    date_hierarchy = 'created_at'

    def problem_code(self, obj):
        return obj.problem.code
    problem_code.short_description = _('Problem')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
