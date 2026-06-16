import json
from operator import attrgetter

from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.forms import ModelForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import filesizeformat
from django.template.response import TemplateResponse
from django.urls import path, reverse_lazy
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy as _, ngettext
from reversion.admin import VersionAdmin

from judge.models import LanguageLimit, Problem, ProblemClarification, ProblemTranslation, Profile, Solution
from judge.models.api_key import AIAPIKey, AI_PROVIDER_MODELS, VISION_PROVIDERS
from judge.views.ai_tag_suggest import call_ai_suggest_tags
from judge.utils.views import NoBatchDeleteMixin
from judge.views.widgets import pdf_statement_uploader
from judge.widgets import AdminHeavySelect2MultipleWidget, AdminHeavySelect2Widget, AdminMartorWidget, \
    AdminSelect2MultipleWidget, AdminSelect2Widget, CheckboxSelectMultipleWithSelectAll


class ProblemForm(ModelForm):
    change_message = forms.CharField(max_length=256, label='Edit reason', required=False)
    statement_file = forms.FileField(
        required=False,
        label=_('Upload PDF statement'),
        help_text=_('Upload a PDF to set the statement URL automatically. Leave blank to keep existing.'),
        widget=forms.ClearableFileInput(attrs={'accept': 'application/pdf'}),
    )

    def __init__(self, *args, **kwargs):
        super(ProblemForm, self).__init__(*args, **kwargs)
        self.fields['authors'].widget.can_add_related = False
        self.fields['curators'].widget.can_add_related = False
        self.fields['suggester'].widget.can_add_related = False
        self.fields['testers'].widget.can_add_related = False
        self.fields['banned_users'].widget.can_add_related = False
        self.fields['change_message'].widget.attrs.update({
            'placeholder': gettext('Describe the changes you made (optional)'),
        })

    def clean_statement_file(self):
        from django.conf import settings
        content = self.files.get('statement_file', None)
        if content is not None:
            allowed_exts = getattr(settings, 'PDF_STATEMENT_SAFE_EXTS', ['pdf'])
            max_size = getattr(settings, 'PDF_STATEMENT_MAX_FILE_SIZE', 10 * 1024 * 1024)
            validator = FileExtensionValidator(allowed_extensions=allowed_exts)
            validator(content)
            if content.size > max_size:
                raise forms.ValidationError(
                    _('File size is too big! Maximum file size is %s') % filesizeformat(max_size),
                )
        return content

    class Meta:
        widgets = {
            'authors': AdminHeavySelect2MultipleWidget(data_view='profile_select2'),
            'curators': AdminHeavySelect2MultipleWidget(data_view='profile_select2'),
            'suggester': AdminHeavySelect2Widget(data_view='profile_select2'),
            'testers': AdminHeavySelect2MultipleWidget(data_view='profile_select2'),
            'banned_users': AdminHeavySelect2MultipleWidget(data_view='profile_select2'),
            'organization': AdminHeavySelect2Widget(data_view='organization_select2'),
            'types': AdminSelect2MultipleWidget,
            'group': AdminSelect2Widget,
            'description': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('problem_preview')}),
        }


class ProblemCreatorListFilter(admin.SimpleListFilter):
    title = parameter_name = 'creator'

    def lookups(self, request, model_admin):
        queryset = Profile.objects.exclude(authored_problems=None).values_list('user__username', flat=True)
        return [(name, name) for name in queryset]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(authors__user__username=self.value())


class LanguageLimitInlineForm(ModelForm):
    class Meta:
        widgets = {'language': AdminSelect2Widget}


class LanguageLimitInline(admin.TabularInline):
    model = LanguageLimit
    fields = ('language', 'time_limit', 'memory_limit')
    form = LanguageLimitInlineForm


class ProblemClarificationForm(ModelForm):
    class Meta:
        widgets = {'description': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('comment_preview')})}


class ProblemClarificationInline(admin.StackedInline):
    model = ProblemClarification
    fields = ('description',)
    form = ProblemClarificationForm
    extra = 0


class ProblemSolutionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProblemSolutionForm, self).__init__(*args, **kwargs)
        self.fields['authors'].widget.can_add_related = False

    class Meta:
        widgets = {
            'authors': AdminHeavySelect2MultipleWidget(data_view='profile_select2'),
            'content': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('solution_preview')}),
        }


class ProblemSolutionInline(admin.StackedInline):
    model = Solution
    fields = ('is_public', 'publish_on', 'authors', 'content')
    form = ProblemSolutionForm
    extra = 0


class ProblemTranslationForm(ModelForm):
    class Meta:
        widgets = {'description': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('problem_preview')})}


class ProblemTranslationInline(admin.StackedInline):
    model = ProblemTranslation
    fields = ('language', 'name', 'description')
    form = ProblemTranslationForm
    extra = 0

    def has_permission_full_markup(self, request, obj=None):
        if not obj:
            return True
        return request.user.has_perm('judge.problem_full_markup') or not obj.is_full_markup

    has_add_permission = has_change_permission = has_delete_permission = has_permission_full_markup


class ProblemAdmin(NoBatchDeleteMixin, VersionAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'code', 'name', 'suggester', 'is_public', 'is_manually_managed', 'date', 'authors',
                'curators', 'testers', 'is_organization_private', 'organization', 'submission_source_visibility_mode',
                'testcase_visibility_mode', 'testcase_result_visibility_mode', 'allow_view_feedback',
                'is_full_markup', 'pdf_url', 'statement_file', 'source', 'description', 'license',
            ),
        }),
        (_('IDE'), {'fields': ('enable_new_ide',)}),
        (_('Social Media'), {'classes': ('collapse',), 'fields': ('og_image', 'summary')}),
        (_('Taxonomy'), {'fields': ('types', 'group')}),
        (_('Points'), {'fields': ('points', 'scoring_mode')}),
        (_('Limits'), {'fields': ('time_limit', 'memory_limit')}),
        (_('Language'), {'fields': ('allowed_languages',)}),
        (_('Justice'), {'fields': ('banned_users',)}),
        (_('History'), {'fields': ('change_message',)}),
    )
    list_display = ['code', 'name', 'show_authors', 'points', 'is_public', 'show_public']
    ordering = ['code']
    search_fields = ('code', 'name', 'authors__user__username', 'curators__user__username')
    inlines = [LanguageLimitInline, ProblemClarificationInline, ProblemSolutionInline, ProblemTranslationInline]
    list_max_show_all = 1000
    actions_on_top = True
    actions_on_bottom = True
    list_filter = ('is_public', ProblemCreatorListFilter)
    form = ProblemForm
    date_hierarchy = 'date'
    change_list_template = 'admin/judge/problem/change_list.html'

    def get_actions(self, request):
        actions = super(ProblemAdmin, self).get_actions(request)

        if request.user.has_perm('judge.change_public_visibility'):
            func, name, desc = self.get_action('make_public_and_update_publish_date')
            actions[name] = (func, name, desc)

            func, name, desc = self.get_action('make_private')
            actions[name] = (func, name, desc)

        return actions

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if not request.user.has_perm('judge.change_public_visibility'):
            fields += ('is_public',)
        if not request.user.has_perm('judge.change_manually_managed'):
            fields += ('is_manually_managed',)
        if not request.user.has_perm('judge.problem_full_markup'):
            fields += ('is_full_markup',)
            if obj and obj.is_full_markup:
                fields += ('description',)
        return fields

    @admin.display(description=_('authors'))
    def show_authors(self, obj):
        return ', '.join(map(attrgetter('user.username'), obj.authors.all()))

    @admin.display(description='')
    def show_public(self, obj):
        return format_html('<a href="{1}">{0}</a>', gettext('View on site'), obj.get_absolute_url())

    def _rescore(self, request, problem_id, publicy_changed=False):
        from judge.tasks import rescore_problem
        transaction.on_commit(rescore_problem.s(problem_id, publicy_changed).delay)

    @admin.display(description=_('Mark problems as public and set publish date to now'))
    def make_public_and_update_publish_date(self, request, queryset):
        count = queryset.update(is_public=True, date=timezone.now())
        for problem_id in queryset.values_list('id', flat=True):
            self._rescore(request, problem_id, True)

        self.message_user(request, ngettext('%d problem successfully marked as public.',
                                            '%d problems successfully marked as public.',
                                            count) % count)

    @admin.display(description=_('Mark problems as private'))
    def make_private(self, request, queryset):
        count = queryset.update(is_public=False)
        for problem_id in queryset.values_list('id', flat=True):
            self._rescore(request, problem_id, True)
        self.message_user(request, ngettext('%d problem successfully marked as private.',
                                            '%d problems successfully marked as private.',
                                            count) % count)

    def get_queryset(self, request):
        return Problem.get_editable_problems(request.user).prefetch_related('authors__user').distinct()

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('judge.edit_own_problem')
        return obj.is_editable_by(request.user)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'allowed_languages':
            kwargs['widget'] = CheckboxSelectMultipleWithSelectAll()
        return super(ProblemAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def get_form(self, *args, **kwargs):
        form = super(ProblemAdmin, self).get_form(*args, **kwargs)
        form.base_fields['authors'].queryset = Profile.objects.all()
        return form

    def save_model(self, request, obj, form, change):
        statement_file = form.cleaned_data.get('statement_file')
        if statement_file:
            obj.pdf_url = pdf_statement_uploader(statement_file)
        super(ProblemAdmin, self).save_model(request, obj, form, change)
        if (
            form.changed_data and
            any(f in form.changed_data for f in ('is_public', 'is_organization_private', 'scoring_mode'))
        ):
            self._rescore(request, obj.id, 'is_public' in form.changed_data)

    def construct_change_message(self, request, form, *args, **kwargs):
        if form.cleaned_data.get('change_message'):
            return form.cleaned_data['change_message']
        return super(ProblemAdmin, self).construct_change_message(request, form, *args, **kwargs)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['ai_provider_models_json'] = json.dumps(AI_PROVIDER_MODELS)
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        return [
            path('<path:object_id>/ai-suggest-tags/',
                 self.admin_site.admin_view(self.ai_suggest_tags_view),
                 name='judge_problem_ai_suggest_tags'),
            path('ai-create/', self.admin_site.admin_view(self.ai_create_problem_view),
                 name='judge_problem_ai_create'),
            path('ai-create/process/', self.admin_site.admin_view(self.ai_create_problem_process),
                 name='judge_problem_ai_create_process'),
        ] + super().get_urls()

    def ai_create_problem_view(self, request):
        if not request.user.has_perm('judge.add_problem'):
            raise PermissionDenied()

        vision_models = {k: v for k, v in AI_PROVIDER_MODELS.items() if k in VISION_PROVIDERS}

        context = {
            **self.admin_site.each_context(request),
            'title': _('Create Problem with AI'),
            'provider_models_json': json.dumps(vision_models),
            'has_permission': True,
        }
        return TemplateResponse(request, 'admin/judge/problem/ai_create.html', context)

    def ai_create_problem_process(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        if not request.user.has_perm('judge.add_problem'):
            raise PermissionDenied()

        from judge.views.ai_problem_creator import call_ai_provider, validate_file

        provider = request.POST.get('provider', '').strip()
        model = request.POST.get('model', '').strip()
        output_language = request.POST.get('output_language', 'English').strip()
        uploaded_file = request.FILES.get('file')

        if provider not in VISION_PROVIDERS:
            return JsonResponse({'error': _('Invalid provider. Must support vision input.')}, status=400)

        valid_models = AI_PROVIDER_MODELS.get(provider, [])
        if model not in valid_models:
            return JsonResponse({'error': _('Invalid model for this provider')}, status=400)

        is_valid, error = validate_file(uploaded_file)
        if not is_valid:
            return JsonResponse({'error': error}, status=400)

        try:
            api_key_obj = AIAPIKey.objects.get(
                user=request.user.profile, provider=provider, status='verified',
            )
        except AIAPIKey.DoesNotExist:
            return JsonResponse({
                'error': _('No verified API key found for %s. Please add and verify one first.') % provider,
            }, status=400)

        plaintext_key = api_key_obj.decrypt_key()
        if not plaintext_key:
            return JsonResponse({'error': _('Failed to decrypt API key')}, status=500)

        success, result = call_ai_provider(provider, model, plaintext_key, uploaded_file, output_language)
        plaintext_key = None  # noqa: F841

        if not success:
            return JsonResponse({'error': result}, status=400)

        api_key_obj.last_used_at = timezone.now()
        api_key_obj.save(update_fields=['last_used_at'])

        return JsonResponse({'success': True, 'description': result})

    def ai_suggest_tags_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)

        problem = get_object_or_404(Problem, pk=object_id)
        if not problem.is_editable_by(request.user):
            raise PermissionDenied()

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': _('Invalid request data')}, status=400)

        provider = body.get('provider', '').strip()
        model = body.get('model', '').strip()

        if provider not in AI_PROVIDER_MODELS:
            return JsonResponse({'error': _('Invalid provider')}, status=400)
        if model not in AI_PROVIDER_MODELS.get(provider, []):
            return JsonResponse({'error': _('Invalid model for this provider')}, status=400)

        try:
            api_key_obj = AIAPIKey.objects.get(
                user=request.user.profile, provider=provider, status='verified',
            )
        except AIAPIKey.DoesNotExist:
            return JsonResponse({
                'error': _('No verified API key for %s. Add one in Settings > AI API Keys.') % provider,
            }, status=400)

        plaintext_key = api_key_obj.decrypt_key()
        if not plaintext_key:
            return JsonResponse({'error': _('Failed to decrypt API key')}, status=500)

        try:
            success, result = call_ai_suggest_tags(problem, provider, model, plaintext_key)
        finally:
            plaintext_key = None  # noqa: F841

        if not success:
            return JsonResponse({'error': result}, status=400)

        api_key_obj.last_used_at = timezone.now()
        api_key_obj.save(update_fields=['last_used_at'])

        return JsonResponse({'success': True, 'tags': result})
