
from django import forms
from django.urls import reverse
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
from .models import CrossConnect, CrossConnectAttachment

__all__ = (
    'CrossConnectAttachmentAddForm',
    'CrossConnectAttachmentFilterForm',
    'CrossConnectAttachmentForm',
    'CrossConnectDeactivateForm',
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
    provider = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        label=_('Provider'),
        selector=True,
        quick_add=True,
    )
    attachment_file = forms.FileField(
        label=_('Attachment file'),
        required=False,
    )
    attachment_name = forms.CharField(
        label=_('Attachment name'),
        max_length=100,
        required=False,
    )
    attachment_description = forms.CharField(
        label=_('Attachment description'),
        max_length=200,
        required=False,
    )
    comments = CommentField()

    fieldsets = (
        FieldSet(
            'cross_connect_id',
            'ritm',
            'status',
            'site',
            'tenant',
            'provider',
            'activation_date',
            'description',
            'comments',
            'tags',
            name=_('Cross Connect'),
        ),
        FieldSet(
            'attachment_file',
            'attachment_name',
            'attachment_description',
            name=_('Initial Attachment'),
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
            'provider',
            'activation_date',
            'description',
            'comments',
            'tags',
        )
        widgets = {
            'activation_date': DatePicker(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and not self.instance.provider_id:
            self.fields['provider'].required = False
        elif not self.instance or not self.instance.pk:
            self.fields['site'].widget.attrs['data-cross-connect-id-url'] = reverse(
                'plugins:netbox_cross_connects:crossconnect_next_id'
            )

    def save(self, commit=True):
        instance = super().save(commit=commit)

        attachment_file = self.cleaned_data.get('attachment_file')
        if commit and attachment_file:
            CrossConnectAttachment.objects.create(
                cross_connect=instance,
                file=attachment_file,
                name=self.cleaned_data.get('attachment_name', ''),
                description=self.cleaned_data.get('attachment_description', ''),
            )

        return instance


class CrossConnectDeactivateForm(forms.Form):
    reason = forms.CharField(
        label=_('Deactivation reason'),
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text=_('This reason will be recorded in the last known path and changelog.'),
    )
    confirm = forms.BooleanField(
        label=_('I understand that the related cables will be permanently deleted.'),
        required=True,
    )


class CrossConnectAttachmentAddForm(NetBoxModelForm):
    cross_connect = DynamicModelMultipleChoiceField(
        queryset=CrossConnect.objects.all(),
        label=_('Cross Connect'),
        required=True,
    )

    fieldsets = (
        FieldSet(
            'cross_connect',
            'file',
            'name',
            'description',
            'tags',
            name=_('Attachment'),
        ),
    )

    class Meta:
        model = CrossConnectAttachment
        fields = (
            'file',
            'name',
            'description',
            'tags',
        )
        help_texts = {
            'name': _('If no name is specified, the uploaded file name will be used.'),
        }


class CrossConnectAttachmentForm(NetBoxModelForm):
    cross_connect = DynamicModelChoiceField(
        queryset=CrossConnect.objects.all(),
        label=_('Cross Connect'),
        selector=True,
        required=True,
    )

    fieldsets = (
        FieldSet(
            'cross_connect',
            'file',
            'name',
            'description',
            'tags',
            name=_('Attachment'),
        ),
    )

    class Meta:
        model = CrossConnectAttachment
        fields = (
            'cross_connect',
            'file',
            'name',
            'description',
            'tags',
        )
        help_texts = {
            'name': _('If no name is specified, the uploaded file name will be used.'),
        }


class CrossConnectAttachmentFilterForm(NetBoxModelFilterSetForm):
    model = CrossConnectAttachment
    fieldsets = (
        FieldSet('q', 'filter_id'),
        FieldSet('cross_connect_id', name=_('Attributes')),
    )
    cross_connect_id = DynamicModelMultipleChoiceField(
        queryset=CrossConnect.objects.all(),
        required=False,
        label=_('Cross Connect'),
    )


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
    provider = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        label=_('Provider'),
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
    attachment_file = forms.FileField(
        label=_('Attachment file'),
        required=False,
    )
    attachment_name = forms.CharField(
        label=_('Attachment name'),
        max_length=100,
        required=False,
    )
    attachment_description = forms.CharField(
        label=_('Attachment description'),
        max_length=200,
        required=False,
    )
    comments = CommentField()

    model = CrossConnect
    fieldsets = (
        FieldSet('status', 'site', 'tenant', 'provider', 'activation_date', 'description', name=_('Cross Connect')),
        FieldSet('attachment_file', 'attachment_name', 'attachment_description', name=_('Attachment')),
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
        FieldSet('status', 'site_id', 'tenant_id', 'provider_id', name=_('Attributes')),
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
    provider_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        label=_('Provider'),
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
    provider = CSVModelChoiceField(
        label=_('Provider'),
        queryset=Tenant.objects.all(),
        to_field_name='name',
        help_text=_('Assigned provider'),
    )

    class Meta:
        model = CrossConnect
        fields = (
            'cross_connect_id',
            'ritm',
            'status',
            'site',
            'tenant',
            'provider',
            'activation_date',
            'last_known_path',
            'description',
            'comments',
            'tags',
        )
