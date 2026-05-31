from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from judge.models.api_key import AIAPIKey, AIAPIKeyTestLog


class AIAPIKeyTestLogInline(admin.TabularInline):
    model = AIAPIKeyTestLog
    extra = 0
    readonly_fields = ('provider', 'model_tested', 'success', 'detail', 'response_time_ms', 'tested_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class AIAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'masked_key', 'status_colored', 'default_model', 'last_used_at', 'added_at')
    list_filter = ('provider', 'status')
    search_fields = ('user__user__username', 'provider', 'key_last4')
    readonly_fields = ('key_last4', 'key_ciphertext', 'added_at', 'last_used_at')
    inlines = [AIAPIKeyTestLogInline]

    def masked_key(self, obj):
        return f'****{obj.key_last4}'
    masked_key.short_description = _('API Key')

    def status_colored(self, obj):
        colors = {'verified': '#2e7d32', 'failed': '#c62828', 'pending': '#f57c00'}
        color = colors.get(obj.status, '#666')
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, obj.get_status_display())
    status_colored.short_description = _('Status')


class AIAPIKeyTestLogAdmin(admin.ModelAdmin):
    list_display = ('api_key', 'provider', 'model_tested', 'success_icon', 'response_time_ms', 'tested_at')
    list_filter = ('provider', 'success')
    search_fields = ('api_key__user__user__username', 'model_tested')
    readonly_fields = ('api_key', 'provider', 'model_tested', 'success', 'detail', 'response_time_ms', 'tested_at')

    def success_icon(self, obj):
        if obj.success:
            return format_html('<span style="color:#2e7d32;">&#10004;</span>')
        return format_html('<span style="color:#c62828;">&#10008;</span>')
    success_icon.short_description = _('Result')

    def has_add_permission(self, request):
        return False
