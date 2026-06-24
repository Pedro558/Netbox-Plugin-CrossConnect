from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Site
from netbox.forms import NetBoxModelBulkEditForm, NetBoxModelFilterSetForm, NetBoxModelForm, NetBoxModelImportForm
from tenancy.models import Tenant
from utilities.forms import add_blank_choice
from utilities.forms.fields import (
    CSVChoiceField,
    CSVModelChoiceField,
    CommentField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.rendering import FieldSet
from utilities.forms.widgets import DatePicker

from .choices import CrossConnectStatusChoices
from .models import CrossConnect

__all__ = (
    'CrossConnectBulkEditForm',
    'CrossConnectFilterForm',
    'CrossConnectForm',
    'CrossConnectImportForm',
)


class CrossConnectForm(NetBoxModelForm):
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
    comments = CommentField()

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
        )
        widgets = {
            'activation_date': DatePicker(),
        }


class CrossConnectBulkEditForm(NetBoxModelBulkEditForm):
    status = forms.ChoiceField(
        label=_('Status'),
        choices=add_blank_choice(CrossConnectStatusChoices),
        required=False,
        initial='',
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label=_('Site'),
    )
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        label=_('Tenant'),
    )
    activation_date = forms.DateField(
        label=_('Activation date'),
        required=False,
        widget=DatePicker(),
    )
    description = forms.CharField(
        label=_('Description'),
        max_length=200,
        required=False,
    )
    comments = CommentField()

    model = CrossConnect
    fieldsets = (
        FieldSet('status', 'site', 'tenant', 'activation_date', 'description', name=_('Cross Connect')),
    )
    nullable_fields = (
        'activation_date',
        'description',
        'comments',
    )


class CrossConnectFilterForm(NetBoxModelFilterSetForm):
    model = CrossConnect
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('status', 'site_id', 'tenant_id', name=_('Attributes')),
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


class CrossConnectImportForm(NetBoxModelImportForm):
    status = CSVChoiceField(
        label=_('Status'),
        choices=CrossConnectStatusChoices,
        help_text=_('Operational status'),
    )
    site = CSVModelChoiceField(
        label=_('Site'),
        queryset=Site.objects.all(),
        to_field_name='name',
        help_text=_('Assigned site'),
    )
    tenant = CSVModelChoiceField(
        label=_('Tenant'),
        queryset=Tenant.objects.all(),
        to_field_name='name',
        help_text=_('Assigned tenant'),
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
            'last_known_path',
            'description',
            'comments',
            'tags',
        )
