
import django_filters
from django.db.models import Q
from django.utils.translation import gettext as _

from dcim.models import Site
from netbox.filtersets import NetBoxModelFilterSet
from tenancy.models import Tenant

from .choices import CrossConnectStatusChoices
from .models import CrossConnect, CrossConnectAttachment

__all__ = ('CrossConnectAttachmentFilterSet', 'CrossConnectFilterSet')


class CrossConnectFilterSet(NetBoxModelFilterSet):
    site_id = django_filters.ModelMultipleChoiceFilter(
        field_name='site',
        queryset=Site.objects.all(),
        label=_('Site'),
    )
    site = django_filters.ModelMultipleChoiceFilter(
        field_name='site__slug',
        queryset=Site.objects.all(),
        to_field_name='slug',
        label=_('Site (slug)'),
    )
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        field_name='tenant',
        queryset=Tenant.objects.all(),
        label=_('Tenant'),
    )
    tenant = django_filters.ModelMultipleChoiceFilter(
        field_name='tenant__slug',
        queryset=Tenant.objects.all(),
        to_field_name='slug',
        label=_('Tenant (slug)'),
    )
    provider_id = django_filters.ModelMultipleChoiceFilter(
        field_name='provider',
        queryset=Tenant.objects.all(),
        label=_('Provider'),
    )
    provider = django_filters.ModelMultipleChoiceFilter(
        field_name='provider__slug',
        queryset=Tenant.objects.all(),
        to_field_name='slug',
        label=_('Provider (slug)'),
    )
    status = django_filters.MultipleChoiceFilter(
        choices=CrossConnectStatusChoices,
    )

    class Meta:
        model = CrossConnect
        fields = (
            'id',
            'cross_connect_id',
            'ritm',
            'status',
            'activation_date',
            'provider_id',
            'provider',
            'last_known_path',
            'description',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(cross_connect_id__icontains=value) |
            Q(ritm__icontains=value) |
            Q(description__icontains=value) |
            Q(comments__icontains=value)
        )


class CrossConnectAttachmentFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(
        method='search',
        label=_('Search'),
    )
    cross_connect_id = django_filters.ModelMultipleChoiceFilter(
        field_name='cross_connect',
        queryset=CrossConnect.objects.all(),
        label=_('Cross Connect'),
    )
    cross_connect = django_filters.ModelMultipleChoiceFilter(
        field_name='cross_connect__cross_connect_id',
        queryset=CrossConnect.objects.all(),
        to_field_name='cross_connect_id',
        label=_('Cross Connect ID'),
    )

    class Meta:
        model = CrossConnectAttachment
        fields = (
            'id',
            'cross_connect_id',
            'cross_connect',
            'name',
            'description',
            'created',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(file__icontains=value) |
            Q(cross_connect__cross_connect_id__icontains=value)
        )
