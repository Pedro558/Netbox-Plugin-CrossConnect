import django_tables2 as tables
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from dcim.models import Cable
from netbox.tables import NetBoxTable, columns

from .models import CrossConnect

__all__ = (
    'CrossConnectTable',
    'RelatedCableTable',
)


class CrossConnectTable(NetBoxTable):
    cross_connect_id = tables.Column(
        linkify=True,
        verbose_name=_('Cross Connect ID'),
    )
    status = columns.ChoiceFieldColumn()
    site = tables.Column(
        linkify=True,
        verbose_name=_('Site'),
    )
    tenant = tables.Column(
        linkify=True,
        verbose_name=_('Tenant'),
    )
    tags = columns.TagColumn(
        url_name='plugins:netbox_cross_connects:crossconnect_list',
    )

    class Meta(NetBoxTable.Meta):
        model = CrossConnect
        fields = (
            'pk',
            'id',
            'cross_connect_id',
            'ritm',
            'status',
            'site',
            'tenant',
            'activation_date',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = (
            'pk',
            'cross_connect_id',
            'ritm',
            'status',
            'site',
            'tenant',
            'activation_date',
            'description',
        )


class CableEndpointsColumn(tables.Column):
    def __init__(self, side, *args, **kwargs):
        self.side = side.lower()
        kwargs.setdefault('empty_values', ())
        super().__init__(*args, **kwargs)

    @staticmethod
    def _termination_label(termination):
        parent = getattr(termination, 'parent_object', None)
        device = getattr(termination, '_device', None) or parent
        site = getattr(termination, '_site', None)
        location = getattr(termination, '_location', None)
        rack = getattr(termination, '_rack', None)

        parts = [str(value) for value in (site, location, rack, device) if value]
        if parts:
            return f'{" : ".join(parts)} > {termination}'.replace(' : ', ':')
        if device:
            return f'{device} > {termination}'
        return str(termination)

    @classmethod
    def _format_termination(cls, termination):
        label = cls._termination_label(termination)
        return f'<a href="{termination.get_absolute_url()}">{escape(label)}</a>'

    def _get_side_terms(self, record):
        return [
            self._format_termination(term)
            for term in getattr(record, f'{self.side}_terminations')
        ]

    def render(self, record):
        terms = ' / '.join(self._get_side_terms(record))
        if not terms:
            return mark_safe('&mdash;')
        return mark_safe(terms)

    def value(self, record):
        return ' / '.join(
            self._termination_label(term)
            for term in getattr(record, f'{self.side}_terminations')
        )


class RelatedCableTable(NetBoxTable):
    cable = tables.TemplateColumn(
        template_code='<a href="{{ record.get_absolute_url }}">{{ record }}</a>',
        verbose_name=_('Cable'),
        orderable=False,
    )
    termination_a = CableEndpointsColumn(
        side='a',
        verbose_name=_('Termination A'),
        orderable=False,
    )
    termination_b = CableEndpointsColumn(
        side='b',
        verbose_name=_('Termination B'),
        orderable=False,
    )
    status = columns.ChoiceFieldColumn()

    class Meta(NetBoxTable.Meta):
        model = Cable
        fields = (
            'cable',
            'termination_a',
            'termination_b',
            'status',
        )
        default_columns = (
            'cable',
            'termination_a',
            'termination_b',
            'status',
        )
