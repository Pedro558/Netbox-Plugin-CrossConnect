from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Site
from netbox.forms import PrimaryModelFilterSetForm, PrimaryModelForm
from tenancy.models import Tenant
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet
from utilities.forms.widgets import DatePicker

from .choices import CrossConnectStatusChoices
from .models import CrossConnect

__all__ = (
    'CrossConnectFilterForm',
    'CrossConnectForm',
)


class CrossConnectForm(PrimaryModelForm):
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        label=_('Site'),
        selector=True,
        quick_add=True,
    )
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        label=_('Tenant'),
        selector=True,
        quick_add=True,
    )

    fieldsets = (
        FieldSet(
            'cross_connect_id',
            'ritm',
            'status',
            'site',
            'tenant',
            'activation_date',
            'description',
            'comments',
            'owner',
            'tags',
            name=_('Cross Connect'),
        ),
    )

    class Meta:
        model = CrossConnect
        fields = (
            'cross_connect_id',
            'ritm',
            'status',
            'site',
            'tenant',
            'activation_date',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {
            'activation_date': DatePicker(),
        }


class CrossConnectFilterForm(PrimaryModelFilterSetForm):
    model = CrossConnect
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('status', 'site_id', 'tenant_id', name=_('Attributes')),
        FieldSet('owner_group_id', 'owner_id', name=_('Ownership')),
    )
    status = forms.MultipleChoiceField(
        choices=CrossConnectStatusChoices,
        required=False,
        label=_('Status'),
    )
    site_id = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label=_('Site'),
    )
    tenant_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        label=_('Tenant'),
    )
    tag = TagFilterField(model)
