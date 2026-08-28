
import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import router, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from core.exceptions import JobFailed
from core.signals import clear_events
from dcim.models import Cable, Interface
from extras.choices import CustomFieldTypeChoices
from extras.models import CustomField
from netbox.object_actions import AddObject, BulkExport
from netbox.views import generic
from utilities.exceptions import AbortRequest, PermissionsViolation
from utilities.forms import restrict_form_fields
from utilities.htmx import htmx_partial
from utilities.jobs import is_background_request, process_request_as_job
from utilities.querydict import normalize_querydict, prepare_cloned_fields
from utilities.request import safe_for_redirect
from utilities.views import register_model_view

from . import filtersets, forms, tables
from .models import CrossConnect, CrossConnectAttachment


def create_attachment_for_cross_connect(cross_connect, upload, name='', description=''):
    upload.seek(0)
    file_content = upload.read()

    attachment = CrossConnectAttachment(
        cross_connect=cross_connect,
        name=name,
        description=description,
    )
    attachment.file.save(upload.name, ContentFile(file_content), save=False)
    attachment.full_clean()
    attachment.save()
    return attachment


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

    @staticmethod
    def _get_next_a_side_type(termination):
        termination_type = termination._meta.label_lower
        return {
            'dcim.frontport': 'dcim.rearport',
            'dcim.rearport': 'dcim.frontport',
        }.get(termination_type, termination_type)

    def _get_add_cable_url(self, cross_connect, related_cables):
        params = {
            'status': 'connected',
            'label': cross_connect.cross_connect_id,
            'tenant': cross_connect.tenant_id,
            'cf_cross_connect': cross_connect.pk,
            'return_url': cross_connect.get_absolute_url(),
        }

        latest_cable = related_cables.order_by('-created', '-pk').first()
        if latest_cable and (b_terminations := latest_cable.b_terminations):
            termination = b_terminations[0]
            if device := getattr(termination, 'device', None):
                params.update({
                    'a_terminations_type': self._get_next_a_side_type(termination),
                    'termination_a_device': device.pk,
                })

        return f"{reverse('dcim:cable_add')}?{urlencode(params)}"

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

        add_cable_url = None
        if related_cables_custom_field and request.user.has_perm('dcim.add_cable'):
            add_cable_url = self._get_add_cable_url(instance, related_cables)

        return {
            'attachments_table': attachments_table,
            'related_cables_custom_field': related_cables_custom_field,
            'related_cables_table': related_cables_table,
            'add_cable_url': add_cable_url,
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
    template_name = 'netbox_cross_connects/crossconnect_bulk_edit.html'

    def post_save_operations(self, form, obj):
        super().post_save_operations(form, obj)

        attachment_file = form.cleaned_data.get('attachment_file')
        if attachment_file:
            create_attachment_for_cross_connect(
                cross_connect=obj,
                upload=attachment_file,
                name=form.cleaned_data.get('attachment_name', ''),
                description=form.cleaned_data.get('attachment_description', ''),
            )

    def post(self, request, **kwargs):
        logger = logging.getLogger('netbox.views.BulkEditView')
        model = self.queryset.model

        if request.POST.get('_all') and self.filterset is not None:
            pk_list = self.filterset(request.GET, self.queryset.values_list('pk', flat=True), request=request).qs
        else:
            pk_list = request.POST.getlist('pk')

        initial_data = {'pk': pk_list}

        post_data = request.POST.copy()
        post_data.setlist('pk', pk_list)
        form = self.form(post_data, files=request.FILES, initial=initial_data)
        restrict_form_fields(form, request.user)

        if '_apply' in request.POST:
            if form.is_valid():
                logger.debug('Form validation was successful')

                if form.cleaned_data['background_job']:
                    job_name = _('Bulk edit {count} {object_type}').format(
                        count=len(form.cleaned_data['pk']),
                        object_type=model._meta.verbose_name_plural,
                    )
                    if process_request_as_job(self.__class__, request, name=job_name):
                        return redirect(self.get_return_url(request))

                try:
                    with transaction.atomic(using=router.db_for_write(model)):
                        updated_objects = self._update_objects(form, request)
                        object_count = self.queryset.filter(pk__in=[obj.pk for obj in updated_objects]).count()
                        if object_count != len(updated_objects):
                            raise PermissionsViolation

                    msg = _('Updated {count} {object_type}').format(
                        count=len(updated_objects),
                        object_type=model._meta.verbose_name_plural,
                    )
                    logger.info(msg)

                    if is_background_request(request):
                        request.job.logger.info(msg)
                        return

                    messages.success(self.request, msg)
                    return redirect(self.get_return_url(request))

                except (AbortRequest, PermissionsViolation, ValidationError) as e:
                    err_messages = e.messages if type(e) is ValidationError else [e.message]
                    for msg in err_messages:
                        logger.debug(msg)
                        form.add_error(None, msg)
                        if is_background_request(request):
                            request.job.logger.error(msg)
                    clear_events.send(sender=self)
                    if is_background_request(request):
                        raise JobFailed

            else:
                logger.debug('Form validation failed')

        table = self.table(self.queryset.filter(pk__in=pk_list), orderable=False)
        if not table.rows:
            messages.warning(
                request,
                _('No {object_type} were selected.').format(object_type=model._meta.verbose_name_plural)
            )
            return redirect(self.get_return_url(request))

        return render(request, self.template_name, {
            'model': model,
            'form': form,
            'table': table,
            'return_url': self.get_return_url(request),
            **self.get_extra_context(request),
        })


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
    filterset = filtersets.CrossConnectAttachmentFilterSet
    filterset_form = forms.CrossConnectAttachmentFilterForm
    table = tables.CrossConnectAttachmentTable
    actions = (AddObject, BulkExport)


@register_model_view(CrossConnectAttachment)
class CrossConnectAttachmentView(generic.ObjectView):
    queryset = CrossConnectAttachment.objects.select_related('cross_connect')
    template_name = 'netbox_cross_connects/crossconnectattachment.html'


@register_model_view(CrossConnectAttachment, 'add', detail=False)
class CrossConnectAttachmentAddView(generic.ObjectEditView):
    queryset = CrossConnectAttachment.objects.select_related('cross_connect')
    form = forms.CrossConnectAttachmentAddForm

    def get(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        initial_data = normalize_querydict(request.GET)
        if cross_connect_id := request.GET.get('cross_connect'):
            initial_data.setlist('cross_connect', [cross_connect_id])
        form = self.form(instance=obj, initial=initial_data)
        restrict_form_fields(form, request.user)

        context = {
            'model': self.queryset.model,
            'object': obj,
            'form': form,
        }

        if request.GET.get('_quickadd'):
            return render(request, 'htmx/quick_add.html', context)
        if htmx_partial(request):
            return render(request, self.htmx_template_name, context)

        return render(request, self.template_name, {
            **context,
            'return_url': self.get_return_url(request, obj),
            'prerequisite_model': None,
            **self.get_extra_context(request, obj),
        })

    def post(self, request, *args, **kwargs):
        logger = logging.getLogger('netbox.views.ObjectEditView')
        obj = self.get_object(**kwargs)
        form = self.form(data=request.POST, files=request.FILES, instance=obj)
        restrict_form_fields(form, request.user)

        if form.is_valid():
            logger.debug('Form validation was successful')
            try:
                with transaction.atomic(using=router.db_for_write(CrossConnectAttachment)):
                    created_attachments = []
                    for cross_connect in form.cleaned_data['cross_connect']:
                        created_attachments.append(
                            create_attachment_for_cross_connect(
                                cross_connect=cross_connect,
                                upload=form.cleaned_data['file'],
                                name=form.cleaned_data.get('name', ''),
                                description=form.cleaned_data.get('description', ''),
                            )
                        )
                        if form.cleaned_data.get('tags'):
                            created_attachments[-1].tags.set(form.cleaned_data['tags'])

                msg = _('Created {count} {object_type}').format(
                    count=len(created_attachments),
                    object_type=CrossConnectAttachment._meta.verbose_name_plural,
                )
                logger.info(msg)
                messages.success(request, msg)

                if '_addanother' in request.POST:
                    redirect_url = request.path
                    params = {}
                    if 'return_url' in request.GET:
                        params['return_url'] = request.GET.get('return_url')
                    if request.GET.get('cross_connect'):
                        params['cross_connect'] = request.GET.get('cross_connect')
                    if params:
                        from django.http import QueryDict
                        q = QueryDict('', mutable=True)
                        for k, v in params.items():
                            q[k] = v
                        redirect_url += f'?{q.urlencode()}'
                    return redirect(redirect_url)

                return redirect(self.get_return_url(request, created_attachments[0]))

            except (AbortRequest, PermissionsViolation, ValidationError) as e:
                err_messages = e.messages if type(e) is ValidationError else [e.message]
                for msg in err_messages:
                    logger.debug(msg)
                    form.add_error(None, msg)
                clear_events.send(sender=self)
        else:
            logger.debug('Form validation failed')

        return render(request, self.template_name, {
            'model': self.queryset.model,
            'object': obj,
            'form': form,
            'return_url': self.get_return_url(request, obj),
            **self.get_extra_context(request, obj),
        })


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
