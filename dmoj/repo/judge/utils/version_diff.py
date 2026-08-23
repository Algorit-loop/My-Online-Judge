"""Turn consecutive django-reversion snapshots into a readable, GitHub-style changelog.

reversion already stores a full JSON snapshot of every tracked object on each save, so no extra
model or migration is needed here: this module only *reads* those snapshots and diffs them. It is
display-only — nothing in it writes to the database or touches the save path.
"""
import datetime
import difflib
import json
from collections import defaultdict

from django.db import models
from django.utils import formats, timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.text import capfirst
from django.utils.translation import gettext, gettext_lazy as _

# Fields the judge/cron updates on its own. They are not human edits, so they would only add noise
# to the history. Keyed by lowercase model name; admin classes may extend this via
# `history_ignore_fields`.
DEFAULT_IGNORE_FIELDS = {
    'problem': ('ac_rate', 'user_count'),
    'profile': ('points', 'performance_points', 'problem_count', 'last_access', 'rating'),
    'contest': ('user_count',),
}

# Revision comments that say nothing about what actually changed. When we see one of these we
# replace it with a generated summary of the changed fields instead.
VAGUE_COMMENTS = frozenset((
    'Edited from site',
    'Chỉnh sửa từ trang web',
    'Changed None.',
    '',
))

# Above this length (or as soon as it spans multiple lines) a text value is rendered as a unified
# diff rather than a plain "old → new" pair.
TEXT_DIFF_THRESHOLD = 80

EMPTY = object()  # field absent from the snapshot, e.g. it did not exist yet at that point in time


class FieldChange:
    """One changed field, already rendered into something a template can print directly."""

    KIND_TEXT = 'text'      # long/multiline value -> unified diff
    KIND_LIST = 'list'      # many-to-many -> added/removed names
    KIND_VALUE = 'value'    # everything else -> old → new

    def __init__(self, name, label, kind, old=None, new=None, diff_lines=None, added=None, removed=None):
        self.name = name
        self.label = label
        self.kind = kind
        self.old = old
        self.new = new
        self.diff_lines = diff_lines or []
        self.added = added or []
        self.removed = removed or []


def _get_fields(version):
    """The `fields` dict of a Version, or None when the payload is unreadable."""
    try:
        return json.loads(version.serialized_data)[0]['fields']
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def _model_field(model, name):
    try:
        return model._meta.get_field(name)
    except Exception:
        return None


def _is_relation(field):
    return field is not None and field.is_relation and field.related_model is not None


def _field_label(field, name):
    """Field name as the current language should show it, capitalised like the rest of the admin.

    A field declared without an explicit verbose_name gets a plain English string derived from its
    attribute name by Django ("problem", "user"), which no translation ever reaches. Those we look
    up in the catalogue by hand — most of them are already translated for other uses. A verbose_name
    that is a lazy object is left alone: it has translated itself already.
    """
    verbose_name = getattr(field, 'verbose_name', None)
    if verbose_name is None:
        # Field dropped from the model by a later migration, so only old snapshots still carry it
        # and there is no metadata left to read. Humanise the raw name and hope the catalogue knows
        # it; either way the history stays readable instead of showing a bare identifier.
        return capfirst(gettext(name.replace('_', ' ')))
    if isinstance(verbose_name, str):
        return capfirst(gettext(verbose_name))
    return capfirst(str(verbose_name))


def _collect_related_ids(model, snapshots, ignored):
    """Walk every snapshot once and bucket the primary keys per related model.

    Doing this up front means one query per related model for the whole page, instead of one query
    (or worse, one per id) inside the render loop.
    """
    wanted = defaultdict(set)
    for fields in snapshots:
        for name, value in fields.items():
            if name in ignored:
                continue
            field = _model_field(model, name)
            if not _is_relation(field):
                continue
            if isinstance(value, (list, tuple)):
                wanted[field.related_model].update(v for v in value if v is not None)
            elif value is not None:
                wanted[field.related_model].add(value)
    return wanted


def _resolve_names(wanted):
    """{related_model: {pk}} -> {(related_model, pk): display name}, one query per model."""
    names = {}
    for related_model, pks in wanted.items():
        if not pks:
            continue
        try:
            for obj in related_model._default_manager.filter(pk__in=pks):
                names[(related_model, obj.pk)] = str(obj)
        except Exception:
            # A related model we cannot query is not worth breaking the history page over; the
            # raw ids are still shown by _name_of() below.
            continue
    return names


def _name_of(names, related_model, pk):
    if pk is None:
        return None
    return names.get((related_model, pk)) or _('#%(pk)s (deleted)') % {'pk': pk}


def _parse_temporal(field, value):
    """The moment a snapshot string stands for, or None when the field is not a date/time one."""
    if not isinstance(value, str):
        return None
    # DateTimeField subclasses DateField, so it has to be tested first.
    if isinstance(field, models.DateTimeField):
        return parse_datetime(value)
    if isinstance(field, models.DateField):
        return parse_date(value)
    return None


def _same_moment(field, old, new):
    """True when two snapshot strings denote the same point in time despite differing as text.

    reversion writes datetimes into the snapshot as ISO strings, and the various save paths render
    the same instant differently — one in UTC with microseconds ("...T09:50:34.606Z"), another in
    local time without them ("...T16:50:34+07:00"). On top of that the admin's datetime widget only
    goes down to the second, so simply opening a change form and pressing save rewrites the field
    with its sub-second part dropped: a difference in the database that is not an edit by anyone.
    Comparing the parsed instants at second precision keeps those non-edits out of the history.
    """
    old_moment, new_moment = _parse_temporal(field, old), _parse_temporal(field, new)
    if old_moment is None or new_moment is None:
        return False
    if isinstance(old_moment, datetime.datetime) and isinstance(new_moment, datetime.datetime):
        # Comparing an aware datetime against a naive one raises; treat that as a real difference.
        if timezone.is_aware(old_moment) != timezone.is_aware(new_moment):
            return False
        return old_moment.replace(microsecond=0) == new_moment.replace(microsecond=0)
    return old_moment == new_moment


def _render_temporal(moment):
    """A date/time in the viewer's timezone, always with seconds.

    Neither locale's DATETIME_FORMAT includes seconds, so formatting with it would render two
    values a few seconds apart as the same text — the very confusion this rendering exists to
    avoid. A numeric format is language-neutral and lines up for eyeball comparison.
    """
    if isinstance(moment, datetime.datetime):
        if timezone.is_aware(moment):
            moment = timezone.localtime(moment)
        return formats.date_format(moment, 'd/m/Y H:i:s')
    return formats.date_format(moment, 'd/m/Y')


def _render_value(model, name, value, names):
    """A single scalar value as it should appear on screen."""
    if value is None:
        return _('(empty)')

    field = _model_field(model, name)
    if _is_relation(field):
        return _name_of(names, field.related_model, value)
    moment = _parse_temporal(field, value)
    if moment is not None:
        return _render_temporal(moment)
    if field is not None and field.choices:
        return dict(field.flatchoices).get(value, value)
    if isinstance(value, bool):
        return _('Yes') if value else _('No')
    if value == '':
        return _('(empty)')
    return value


def _unified_diff(old, new):
    old_lines = str(old or '').splitlines()
    new_lines = str(new or '').splitlines()
    lines = []
    for line in difflib.unified_diff(old_lines, new_lines, lineterm='', n=3):
        if line.startswith('---') or line.startswith('+++'):
            continue
        if line.startswith('@@'):
            kind = 'hunk'
        elif line.startswith('+'):
            kind = 'add'
        elif line.startswith('-'):
            kind = 'del'
        else:
            kind = 'ctx'
        lines.append({'kind': kind, 'text': line})
    return lines


def _looks_like_text(field, old, new):
    if field is not None and isinstance(field, (models.TextField,)):
        return True
    for value in (old, new):
        if isinstance(value, str) and ('\n' in value or len(value) > TEXT_DIFF_THRESHOLD):
            return True
    return False


def diff_snapshots(model, old_fields, new_fields, names, ignored=()):
    """Compare two snapshots of the same model. Returns a list of FieldChange, in model field order.

    A field missing from `old_fields` did not exist on the model back then (it was added by a later
    migration), so it is reported as "no data" rather than as a change from empty.
    """
    changes = []
    for name in new_fields:
        if name in ignored:
            continue

        new_value = new_fields[name]
        old_value = old_fields.get(name, EMPTY) if old_fields is not None else EMPTY
        field = _model_field(model, name)
        if old_value is not EMPTY and (old_value == new_value or _same_moment(field, old_value, new_value)):
            continue

        label = _field_label(field, name)

        if isinstance(field, models.ManyToManyField):
            old_ids = [] if old_value is EMPTY else list(old_value or [])
            new_ids = list(new_value or [])
            added = [_name_of(names, field.related_model, pk) for pk in new_ids if pk not in old_ids]
            removed = [_name_of(names, field.related_model, pk) for pk in old_ids if pk not in new_ids]
            if not added and not removed:
                continue
            changes.append(FieldChange(name, label, FieldChange.KIND_LIST, added=added, removed=removed))
            continue

        if old_value is EMPTY:
            changes.append(FieldChange(
                name, label, FieldChange.KIND_VALUE,
                old=_('(field did not exist yet)'),
                new=_render_value(model, name, new_value, names),
            ))
            continue

        if _looks_like_text(field, old_value, new_value):
            changes.append(FieldChange(
                name, label, FieldChange.KIND_TEXT,
                diff_lines=_unified_diff(old_value, new_value),
            ))
            continue

        changes.append(FieldChange(
            name, label, FieldChange.KIND_VALUE,
            old=_render_value(model, name, old_value, names),
            new=_render_value(model, name, new_value, names),
        ))

    return changes


def summarize(changes, limit=4):
    """Short one-liner for the list column, e.g. "points, time limit and 2 more"."""
    if not changes:
        return ''
    labels = [c.label for c in changes]
    if len(labels) <= limit:
        return ', '.join(labels)
    return _('%(fields)s and %(count)d more') % {
        'fields': ', '.join(labels[:limit]),
        'count': len(labels) - limit,
    }


def describe_action(comment, changes, is_initial):
    """The "Action" column.

    Meaningful comments set by the site ("Cloned problem from x", "Rejudged", ...) are kept as-is.
    Only the uselessly generic ones get replaced by a generated summary, which is why this runs at
    display time: every revision already in the database benefits, and no save path changes.
    """
    comment = (comment or '').strip()
    if comment not in VAGUE_COMMENTS:
        return comment
    if is_initial:
        return str(_('Earliest recorded version'))
    if not changes:
        return str(_('Saved without any change'))
    return str(_('Edited: %(fields)s')) % {'fields': summarize(changes)}


def build_history(model, versions, ignored=()):
    """Diff each Version against the one saved immediately before it.

    Returns a list of dicts aligned 1:1 with `versions`, in the order they were given. The
    predecessor of a version is worked out from its timestamp rather than from its position in
    that list: VersionAdmin sorts the history with an empty `order_by()`, so the order it hands us
    is whatever the database felt like returning and must not be treated as chronological.
    """
    versions = list(versions)
    ignored = frozenset(ignored) | frozenset(DEFAULT_IGNORE_FIELDS.get(model._meta.model_name, ()))
    snapshots = {version.pk: _get_fields(version) for version in versions}
    names = _resolve_names(_collect_related_ids(model, [s for s in snapshots.values() if s], ignored))

    chronological = sorted(versions, key=lambda version: (version.revision.date_created, version.pk))
    predecessor = {newer.pk: older.pk for older, newer in zip(chronological, chronological[1:])}
    earliest_pk = chronological[0].pk if chronological else None

    entries = []
    for version in versions:
        new_fields = snapshots[version.pk]
        is_initial = version.pk == earliest_pk

        if new_fields is None:
            entries.append({'changes': [], 'summary': '', 'is_initial': is_initial, 'unreadable': True})
            continue

        older = snapshots.get(predecessor.get(version.pk))
        changes = diff_snapshots(model, older, new_fields, names, ignored) if older is not None else []
        entries.append({
            'changes': changes,
            'summary': summarize(changes),
            'is_initial': is_initial,
            'unreadable': False,
        })
    return entries
