from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from judge.models.ai_prompt import AIPromptTemplate


class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'updated_at')
    search_fields = ('key', 'name')
    readonly_fields = ('updated_at',)

    fieldsets = (
        (None, {
            'fields': ('key', 'name'),
        }),
        (_('Prompt'), {
            'fields': ('prompt_text', 'description'),
        }),
        (_('Metadata'), {
            'fields': ('updated_at',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('key',)
        return self.readonly_fields
