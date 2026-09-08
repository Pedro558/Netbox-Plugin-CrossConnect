
from dcim.api.serializers_.sites import SiteSerializer
from netbox.api.fields import ChoiceField
from rest_framework import serializers
from netbox.api.serializers import NetBoxModelSerializer
from tenancy.api.serializers_.tenants import TenantSerializer
from django.utils.translation import gettext_lazy as _

from netbox_cross_connects.choices import CrossConnectReviewChoices, CrossConnectStatusChoices
from netbox_cross_connects.models import CrossConnect, CrossConnectAttachment

__all__ = ('CrossConnectAttachmentSerializer', 'CrossConnectSerializer')


class CrossConnectSerializer(NetBoxModelSerializer):
    status = ChoiceField(choices=CrossConnectStatusChoices, required=False)
    cross_review = ChoiceField(choices=CrossConnectReviewChoices, required=False)
    site = SiteSerializer(nested=True)
    tenant = TenantSerializer(nested=True)
    provider = TenantSerializer(nested=True, required=False, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is None and not attrs.get('provider'):
            raise serializers.ValidationError({
                'provider': _('Provider is required when creating a cross connect.'),
            })
        return attrs

    class Meta:
        model = CrossConnect
        fields = [
            'id', 'url', 'display_url', 'display', 'cross_connect_id', 'ritm', 'status', 'cross_review', 'site', 'tenant', 'provider',
            'activation_date', 'last_known_path', 'description', 'comments', 'tags', 'custom_fields', 'created',
            'last_updated',
        ]
        brief_fields = ('id', 'url', 'display', 'cross_connect_id', 'ritm', 'status', 'cross_review', 'description')


class CrossConnectAttachmentSerializer(NetBoxModelSerializer):
    cross_connect = CrossConnectSerializer(nested=True)

    class Meta:
        model = CrossConnectAttachment
        fields = [
            'id', 'url', 'display_url', 'display', 'cross_connect', 'file', 'name', 'description', 'tags',
            'custom_fields', 'created', 'last_updated',
        ]
        brief_fields = ('id', 'url', 'display', 'name', 'description')
