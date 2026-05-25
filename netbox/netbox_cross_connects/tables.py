import django_tables2 as tables
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from dcim.models import Cable
from netbox.tables import NetBoxTable, PrimaryModelTable, columns

from .models import CrossConnect

__all__ = (
    'CrossConnectTable',
    'RelatedCableTable',
)


class CrossConnectTable(PrimaryModelTable):
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

    class Meta(PrimaryModelTable.Meta):
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
    def _format_termination(self, termination):
        device = getattr(termination, '_device', None)
        label = f'{device}/{termination}' if device else str(termination)
        return f'<a href="{termination.get_absolute_url()}">{escape(label)}</a>'

    def _get_side_terms(self, record, side):
        return [
            self._format_termination(term)
            for term in getattr(record, f'{side.lower()}_terminations')
        ]

    def render(self, record):
        a_side = ' / '.join(self._get_side_terms(record, 'A'))
        b_side = ' / '.join(self._get_side_terms(record, 'B'))
        if not a_side and not b_side:
            return mark_safe('&mdash;')
        return mark_safe(f'{a_side} &rarr; {b_side}')

    def value(self, record):
        def _plain(side):
            values = []
            for termination in getattr(record, f'{side.lower()}_terminations'):
                device = getattr(termination, '_device', None)
                values.append(f'{device}/{termination}' if device else str(termination))
            return ' / '.join(values)

        return f'{_plain("A")} -> {_plain("B")}'


class RelatedCableTable(NetBoxTable):
    cable = tables.TemplateColumn(
        template_code='<a href="{{ record.get_absolute_url }}">{{ record }}</a>',
        verbose_name=_('Cable'),
        orderable=False,
    )
    endpoints = CableEndpointsColumn(
        verbose_name=_('Path'),
        orderable=False,
    )
    status = columns.ChoiceFieldColumn()

    class Meta(NetBoxTable.Meta):
        model = Cable
        fields = (
            'cable',
            'endpoints',
            'status',
        )
        default_columns = (
            'cable',
            'endpoints',
            'status',
        )
