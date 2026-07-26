from django.contrib.admin.utils import unquote
from django.shortcuts import get_object_or_404
from reversion.admin import VersionAdmin
from reversion.models import Version
from reversion.revisions import _get_options

from judge.utils.version_diff import build_history, describe_action


class DiffVersionAdmin(VersionAdmin):
    """VersionAdmin whose history page shows *what* changed, not just that something changed.

    Everything happens while rendering: we read the snapshots reversion already stores and diff
    each one against its predecessor. No model, no migration, and no change to how revisions are
    written — so revisions recorded long before this feature existed get the same treatment.
    """

    object_history_template = 'admin/judge/object_history.html'

    # Extra fields to leave out of the diff on top of judge.utils.version_diff.DEFAULT_IGNORE_FIELDS.
    history_ignore_fields = ()

    def _history_versions(self, request, object_id):
        """The same versions, in the same order, that VersionAdmin.history_view lists."""
        version_opts = _get_options(self.model)
        if version_opts.object_id_field == self.model._meta.pk.attname:
            reversion_object_id = unquote(object_id)
        else:
            obj = get_object_or_404(self.model, pk=unquote(object_id))
            reversion_object_id = str(getattr(obj, version_opts.object_id_field))

        return self._reversion_order_version_queryset(
            request,
            Version.objects.get_for_object_reference(self.model, reversion_object_id)
                           .select_related('revision', 'revision__user'),
        )

    def history_view(self, request, object_id, extra_context=None):
        response = super().history_view(request, object_id, extra_context)

        # Anything other than the expected TemplateResponse (a redirect, a permission error page)
        # is passed straight through: the diff is a nicety, never a reason to break the page.
        action_list = getattr(response, 'context_data', {}).get('action_list')
        if not action_list:
            return response

        versions = list(self._history_versions(request, object_id))
        by_revision = {version.revision_id: version for version in versions}

        # history_view builds action_list from the same queryset, but re-align by revision id
        # rather than trusting the two lists to be index-for-index identical.
        aligned = [by_revision.get(action['revision'].id) for action in action_list]
        if any(version is None for version in aligned):
            return response

        entries = build_history(self.model, aligned, self.history_ignore_fields)
        for action, entry in zip(action_list, entries):
            action['changes'] = entry['changes']
            action['summary'] = entry['summary']
            action['unreadable'] = entry['unreadable']
            action['is_initial'] = entry['is_initial']
            action['action_label'] = describe_action(
                action['revision'].get_comment(), entry['changes'], entry['is_initial'],
            )
        return response
