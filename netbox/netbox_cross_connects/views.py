from collections import OrderedDict
from urllib.parse import urlencode

from core.models import ObjectType
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from dcim.models import Cable, Interface
from extras.choices import CustomFieldTypeChoices
from extras.models import CustomField
from extras.ui.panels import CustomFieldsPanel, TagsPanel
from netbox.ui import layout
from netbox.ui.panels import CommentsPanel, TemplatePanel
from netbox.views import generic
from utilities.views import register_model_view

from . import filtersets, forms, tables
from .models import CrossConnect
from .ui import panels


@register_model_view(CrossConnect, 'list', path='', detail=False)
class CrossConnectListView(generic.ObjectListView):
    queryset = CrossConnect.objects.all()
    filterset = filtersets.CrossConnectFilterSet
    filterset_form = forms.CrossConnectFilterForm
    table = tables.CrossConnectTable


@register_model_view(CrossConnect)
class CrossConnectView(generic.ObjectView):
    queryset = CrossConnect.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            panels.CrossConnectPanel(),
            TagsPanel(),
            CommentsPanel(),
        ],
        right_panels=[
            CustomFieldsPanel(),
        ],
        bottom_panels=[
            TemplatePanel('netbox_cross_connects/panels/trace.html', title=_('Trace')),
            TemplatePanel('netbox_cross_connects/panels/related_cables.html', title=_('Related Cables')),
        ],
    )

    @staticmethod
    def _get_related_cables_custom_field():
        cable_type = ObjectType.objects.get_for_model(Cable)

        return CustomField.objects.filter(
            name='cross_connect',
            object_types=cable_type,
            type=CustomFieldTypeChoices.TYPE_OBJECT,
            related_object_type=ObjectType.objects.get_for_model(CrossConnect),
        ).first()

    @staticmethod
    def _get_related_cables(request, instance):
        return Cable.objects.restrict(request.user, 'view').filter(
            custom_field_data__cross_connect=instance.pk
        ).prefetch_related('terminations__termination')

    @staticmethod
    def _resolve_trace(request, related_cables):
        if not request.user.has_perm('dcim.view_interface'):
            return {
                'trace_status': 'unavailable',
                'trace_message': _('Trace requires permission to view interfaces.'),
                'trace_origin_interface': None,
                'trace_destination_interface': None,
                'trace_url': None,
                'trace_svg_url': None,
                'trace_links': [],
            }

        endpoint_interfaces = OrderedDict()
        a_side_interface_ids = set()

        for cable in related_cables:
            for termination in cable.a_terminations:
                if isinstance(termination, Interface):
                    endpoint_interfaces.setdefault(termination.pk, termination)
                    a_side_interface_ids.add(termination.pk)
            for termination in cable.b_terminations:
                if isinstance(termination, Interface):
                    endpoint_interfaces.setdefault(termination.pk, termination)

        endpoint_interfaces = list(endpoint_interfaces.values())
        if len(endpoint_interfaces) != 2:
            return {
                'trace_status': 'unavailable',
                'trace_message': _(
                    'Trace resolution requires exactly two endpoint interfaces across the related cables.'
                ),
                'trace_origin_interface': None,
                'trace_destination_interface': None,
                'trace_url': None,
                'trace_svg_url': None,
                'trace_links': [],
            }

        related_cable_ids = {cable.pk for cable in related_cables}
        valid_candidates = []

        for interface in endpoint_interfaces:
            other_interface = next(candidate for candidate in endpoint_interfaces if candidate.pk != interface.pk)
            path = interface.path
            if path is None or not path.is_complete:
                continue
            if set(path.get_cable_ids()) != related_cable_ids:
                continue
            if len(path.destinations) != 1 or path.destinations[0].pk != other_interface.pk:
                continue

            valid_candidates.append({
                'interface': interface,
                'other_interface': other_interface,
                'trace_url': reverse('dcim:interface_trace', kwargs={'pk': interface.pk}),
                'trace_svg_url': (
                    f"{reverse('dcim-api:interface-trace', kwargs={'pk': interface.pk})}?render=svg"
                ),
            })

        if len(valid_candidates) != 2:
            return {
                'trace_status': 'unavailable',
                'trace_message': _(
                    'NetBox could not match the related cables to one complete native cable path between two interfaces.'
                ),
                'trace_origin_interface': None,
                'trace_destination_interface': None,
                'trace_url': None,
                'trace_svg_url': None,
                'trace_links': [],
            }

        canonical_candidates = [
            candidate for candidate in valid_candidates if candidate['interface'].pk in a_side_interface_ids
        ]
        if len(canonical_candidates) == 1:
            candidate = canonical_candidates[0]
            return {
                'trace_status': 'ready',
                'trace_message': _(
                    'Trace resolved using NetBox native cable tracing from the A-side endpoint interface.'
                ),
                'trace_origin_interface': candidate['interface'],
                'trace_destination_interface': candidate['other_interface'],
                'trace_url': candidate['trace_url'],
                'trace_svg_url': candidate['trace_svg_url'],
                'trace_links': [
                    {
                        'interface': candidate['interface'],
                        'url': candidate['trace_url'],
                    }
                ],
            }

        return {
            'trace_status': 'ambiguous',
            'trace_message': _(
                'A complete cable path exists, but the CrossConnect does not identify one unambiguous A-side interface.'
            ),
            'trace_origin_interface': None,
            'trace_destination_interface': None,
            'trace_url': None,
            'trace_svg_url': None,
            'trace_links': [
                {
                    'interface': candidate['interface'],
                    'url': candidate['trace_url'],
                }
                for candidate in valid_candidates
            ],
        }

    @staticmethod
    def _add_cross_connect_trace_context(trace_context, instance):
        if trace_context.get('trace_url'):
            trace_context['trace_url'] = (
                f"{trace_context['trace_url']}?{urlencode({'cross_connect': instance.pk})}"
            )

        if trace_context.get('trace_links'):
            trace_context['trace_links'] = [
                {
                    **link,
                    'url': f"{link['url']}?{urlencode({'cross_connect': instance.pk})}",
                }
                for link in trace_context['trace_links']
            ]

        return trace_context

    def get_extra_context(self, request, instance):
        related_cables_custom_field = self._get_related_cables_custom_field()
        related_cables_table = None
        trace_context = {
            'trace_status': 'unavailable',
            'trace_message': _('Create cable relationships before tracing this CrossConnect.'),
            'trace_origin_interface': None,
            'trace_destination_interface': None,
            'trace_url': None,
            'trace_svg_url': None,
            'trace_links': [],
        }

        if related_cables_custom_field:
            related_cables = list(self._get_related_cables(request, instance))
            related_cables_table = tables.RelatedCableTable(related_cables)
            related_cables_table.configure(request)
            if related_cables:
                trace_context = self._resolve_trace(request, related_cables)
                trace_context = self._add_cross_connect_trace_context(trace_context, instance)
            else:
                trace_context['trace_message'] = _('No related cables are linked to this CrossConnect.')

        return {
            'related_cables_custom_field': related_cables_custom_field,
            'related_cables_table': related_cables_table,
            **trace_context,
        }


@register_model_view(CrossConnect, 'add', detail=False)
@register_model_view(CrossConnect, 'edit')
class CrossConnectEditView(generic.ObjectEditView):
    queryset = CrossConnect.objects.all()
    form = forms.CrossConnectForm


@register_model_view(CrossConnect, 'delete')
class CrossConnectDeleteView(generic.ObjectDeleteView):
    queryset = CrossConnect.objects.all()
