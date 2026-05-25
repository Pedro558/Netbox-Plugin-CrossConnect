from django.utils.translation import gettext_lazy as _

from dcim.models import Cable
from extras.ui.panels import CustomFieldsPanel, TagsPanel
from netbox.ui import layout
from netbox.ui.panels import CommentsPanel, ContextTablePanel
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
            ContextTablePanel('related_cables_table', title=_('Related Cables')),
        ],
    )

    def get_extra_context(self, request, instance):
        related_cables = Cable.objects.restrict(request.user, 'view').filter(
            custom_field_data__cross_connect=instance.pk
        )
        related_cables_table = tables.RelatedCableTable(related_cables)
        related_cables_table.configure(request)

        return {
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
