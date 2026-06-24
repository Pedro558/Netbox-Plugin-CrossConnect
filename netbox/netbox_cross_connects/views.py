
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _

from dcim.models import Cable, Interface
from extras.choices import CustomFieldTypeChoices
from extras.models import CustomField
from netbox.object_actions import AddObject, BulkExport
from netbox.views import generic
from utilities.views import register_model_view

from . import filtersets, forms, tables
from .models import CrossConnect, CrossConnectAttachment


@register_model_view(CrossConnect, 'list', path='', detail=False)
class CrossConnectListView(generic.ObjectListView):
    queryset = CrossConnect.objects.all()
    filterset = filtersets.CrossConnectFilterSet
    filterset_form = forms.CrossConnectFilterForm
    table = tables.CrossConnectTable


@register_model_view(CrossConnect)
class CrossConnectView(generic.ObjectView):
    queryset = CrossConnect.objects.all()
    template_name = 'netbox_cross_connects/crossconnect.html'

    def _get_related_cables_custom_field(self):
        return (
            CustomField.objects.filter(
                name='cross_connect',
                type=CustomFieldTypeChoices.TYPE_OBJECT,
                related_object_type__app_label='netbox_cross_connects',
                related_object_type__model='crossconnect',
                object_types__app_label='dcim',
                object_types__model='cable',
            )
            .distinct()
            .first()
        )

    def _get_related_cables(self, request, cross_connect):
        if not request.user.has_perm('dcim.view_cable'):
            return Cable.objects.none()

        return (
            Cable.objects.restrict(request.user, 'view')
            .filter(custom_field_data__cross_connect=cross_connect.pk)
            .prefetch_related('terminations', 'terminations__termination')
        )

    def _get_attachments(self, request, cross_connect):
        if not request.user.has_perm('netbox_cross_connects.view_crossconnectattachment'):
            return CrossConnectAttachment.objects.none()

        return (
            CrossConnectAttachment.objects.restrict(request.user, 'view')
            .filter(cross_connect=cross_connect)
            .select_related('cross_connect')
        )

    @staticmethod
    def _get_interface_sides(cables):
        interface_sides = {}

        for cable in cables:
            for termination in cable.a_terminations:
                if isinstance(termination, Interface):
                    interface_sides.setdefault(termination, set()).add('A')
            for termination in cable.b_terminations:
                if isinstance(termination, Interface):
                    interface_sides.setdefault(termination, set()).add('B')

        return interface_sides

    def _get_trace_context(self, request, cross_connect, related_cables):
        related_cables = list(related_cables)
        related_cable_ids = {cable.pk for cable in related_cables}
        default_context = {
            'trace_status': 'unavailable',
            'trace_message': _('Trace is unavailable until exactly two endpoint interfaces can be inferred.'),
            'trace_links': [],
            'trace_origin_interface': None,
            'trace_destination_interface': None,
            'trace_url': None,
            'trace_svg_url': None,
        }

        if not request.user.has_perm('dcim.view_interface'):
            default_context['trace_message'] = _('Permission to view interfaces is required to trace this cross connect.')
            return default_context

        if not related_cable_ids:
            default_context['trace_message'] = _('Trace requires at least one related cable.')
            return default_context

        interface_sides = self._get_interface_sides(related_cables)
        interfaces = list(interface_sides)

        if len(interfaces) != 2:
            default_context['trace_message'] = _('Trace requires exactly two endpoint interfaces on related cables.')
            return default_context

        a_side_interfaces = [interface for interface, sides in interface_sides.items() if sides == {'A'}]
        b_side_interfaces = [interface for interface, sides in interface_sides.items() if sides == {'B'}]

        if len(a_side_interfaces) == 1 and len(b_side_interfaces) == 1:
            origin = a_side_interfaces[0]
            destination = b_side_interfaces[0]

            if not origin.path or not origin.path.is_complete:
                default_context['trace_message'] = _('Native trace path is incomplete for this cross connect.')
                return default_context

            if destination not in origin.path.destinations:
                default_context['trace_message'] = _('Native trace path does not end at the expected interface.')
                return default_context

            if set(origin.path.get_cable_ids()) != related_cable_ids:
                default_context['trace_message'] = _('Native trace path does not match the related cables for this cross connect.')
                return default_context

            trace_url = reverse('dcim:interface_trace', kwargs={'pk': origin.pk})
            trace_svg_url = f"{reverse('dcim-api:interface-trace', kwargs={'pk': origin.pk})}?render=svg"
            return {
                **default_context,
                'trace_status': 'ready',
                'trace_message': _('Native trace is available.'),
                'trace_origin_interface': origin,
                'trace_destination_interface': destination,
                'trace_url': trace_url,
                'trace_svg_url': trace_svg_url,
            }

        return {
            **default_context,
            'trace_status': 'ambiguous',
            'trace_message': _('Trace direction is ambiguous because the endpoint interfaces are not one A-side and one B-side.'),
            'trace_links': [
                {
                    'interface': interface,
                    'url': reverse('dcim:interface_trace', kwargs={'pk': interface.pk}),
                }
                for interface in interfaces
            ],
        }

    def get_extra_context(self, request, instance):
        related_cables_custom_field = self._get_related_cables_custom_field()
        related_cables = Cable.objects.none()
        related_cables_table = None
        attachments = self._get_attachments(request, instance)
        attachments_table = tables.CrossConnectAttachmentEmbeddedTable(attachments, user=request.user)
        attachments_table.configure(request)

        if related_cables_custom_field:
            related_cables = self._get_related_cables(request, instance)
            related_cables_table = tables.RelatedCableTable(related_cables, user=request.user)
            related_cables_table.configure(request)

        return {
            'attachments_table': attachments_table,
            'related_cables_custom_field': related_cables_custom_field,
            'related_cables_table': related_cables_table,
            **self._get_trace_context(request, instance, related_cables),
        }


@register_model_view(CrossConnect, 'add', detail=False)
@register_model_view(CrossConnect, 'edit')
class CrossConnectEditView(generic.ObjectEditView):
    queryset = CrossConnect.objects.all()
    form = forms.CrossConnectForm


@register_model_view(CrossConnect, 'bulk_import', path='import', detail=False)
class CrossConnectBulkImportView(generic.BulkImportView):
    queryset = CrossConnect.objects.all()
    model_form = forms.CrossConnectImportForm


@register_model_view(CrossConnect, 'bulk_edit', path='edit', detail=False)
class CrossConnectBulkEditView(generic.BulkEditView):
    queryset = CrossConnect.objects.all()
    filterset = filtersets.CrossConnectFilterSet
    table = tables.CrossConnectTable
    form = forms.CrossConnectBulkEditForm


@register_model_view(CrossConnect, 'bulk_rename', path='rename', detail=False)
class CrossConnectBulkRenameView(generic.BulkRenameView):
    queryset = CrossConnect.objects.all()
    field_name = 'cross_connect_id'
    filterset = filtersets.CrossConnectFilterSet


@register_model_view(CrossConnect, 'bulk_delete', path='delete', detail=False)
class CrossConnectBulkDeleteView(generic.BulkDeleteView):
    queryset = CrossConnect.objects.all()
    filterset = filtersets.CrossConnectFilterSet
    table = tables.CrossConnectTable


@register_model_view(CrossConnect, 'delete')
class CrossConnectDeleteView(generic.ObjectDeleteView):
    queryset = CrossConnect.objects.all()


@register_model_view(CrossConnectAttachment, 'list', path='', detail=False)
class CrossConnectAttachmentListView(generic.ObjectListView):
    queryset = CrossConnectAttachment.objects.select_related('cross_connect')
    table = tables.CrossConnectAttachmentTable
    actions = (AddObject, BulkExport)


@register_model_view(CrossConnectAttachment)
class CrossConnectAttachmentView(generic.ObjectView):
    queryset = CrossConnectAttachment.objects.select_related('cross_connect')
    template_name = 'netbox_cross_connects/crossconnectattachment.html'


@register_model_view(CrossConnectAttachment, 'add', detail=False)
@register_model_view(CrossConnectAttachment, 'edit')
class CrossConnectAttachmentEditView(generic.ObjectEditView):
    queryset = CrossConnectAttachment.objects.select_related('cross_connect')
    form = forms.CrossConnectAttachmentForm

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk and request.GET.get('cross_connect'):
            cross_connect_id = request.GET.get('cross_connect')
            instance.cross_connect = get_object_or_404(
                CrossConnect.objects.restrict(request.user, 'view'),
                pk=cross_connect_id,
            )
        return instance

    def get_extra_addanother_params(self, request):
        cross_connect_id = request.GET.get('cross_connect')
        return {'cross_connect': cross_connect_id} if cross_connect_id else {}


@register_model_view(CrossConnectAttachment, 'delete')
class CrossConnectAttachmentDeleteView(generic.ObjectDeleteView):
    queryset = CrossConnectAttachment.objects.select_related('cross_connect')
