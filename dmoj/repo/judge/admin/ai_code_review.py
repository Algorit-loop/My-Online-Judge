from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from judge.models.ai_code_review import AICodeReview


class AICodeReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'submission_link', 'provider', 'model', 'output_language', 'created_at')
    list_filter = ('provider', 'output_language', 'created_at')
    search_fields = ('user__user__username', 'provider', 'model')
    readonly_fields = ('user', 'submission', 'provider', 'model', 'review_text', 'output_language', 'created_at')
    date_hierarchy = 'created_at'

    def submission_link(self, obj):
        return f'#{obj.submission_id}'
    submission_link.short_description = _('Submission')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
