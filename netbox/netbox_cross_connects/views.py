from netbox.views import generic
from utilities.views import register_model_view

from . import filtersets, forms, tables
from .models import CrossConnect


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


@register_model_view(CrossConnect, 'add', detail=False)
@register_model_view(CrossConnect, 'edit')
class CrossConnectEditView(generic.ObjectEditView):
    queryset = CrossConnect.objects.all()
    form = forms.CrossConnectForm


@register_model_view(CrossConnect, 'bulk_import', path='import', detail=False)
class CrossConnectBulkImportView(generic.BulkImportView):
    queryset = CrossConnect.objects.all()
    model_form = forms.CrossConnectImportForm


@register_model_view(CrossConnect, 'delete')
class CrossConnectDeleteView(generic.ObjectDeleteView):
    queryset = CrossConnect.objects.all()
