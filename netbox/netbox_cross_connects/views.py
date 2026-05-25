from core.models import ObjectType
from django.utils.translation import gettext_lazy as _

from dcim.models import Cable
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

    def get_extra_context(self, request, instance):
        related_cables_custom_field = self._get_related_cables_custom_field()
        related_cables_table = None

        if related_cables_custom_field:
            related_cables = Cable.objects.restrict(request.user, 'view').filter(
                custom_field_data__cross_connect=instance.pk
            )
            related_cables_table = tables.RelatedCableTable(related_cables)
            related_cables_table.configure(request)

        return {
            'related_cables_custom_field': related_cables_custom_field,
            'related_cables_table': related_cables_table,
        }


@register_model_view(CrossConnect, 'add', detail=False)
@register_model_view(CrossConnect, 'edit')
class CrossConnectEditView(generic.ObjectEditView):
    queryset = CrossConnect.objects.all()
    form = forms.CrossConnectForm


@register_model_view(CrossConnect, 'delete')
class CrossConnectDeleteView(generic.ObjectDeleteView):
    queryset = CrossConnect.objects.all()
