import django_filters
from django.db.models import Q
from django.utils.translation import gettext as _

from dcim.models import Site
from netbox.filtersets import PrimaryModelFilterSet
from tenancy.models import Tenant
from utilities.filtersets import register_filterset

from .choices import CrossConnectStatusChoices
from .models import CrossConnect

__all__ = ('CrossConnectFilterSet',)


@register_filterset
class CrossConnectFilterSet(PrimaryModelFilterSet):
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
