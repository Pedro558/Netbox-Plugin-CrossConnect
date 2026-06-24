
from dcim.api.serializers_.sites import SiteSerializer
from netbox.api.fields import ChoiceField
from netbox.api.serializers import NetBoxModelSerializer
from tenancy.api.serializers_.tenants import TenantSerializer

from netbox_cross_connects.choices import CrossConnectStatusChoices
from netbox_cross_connects.models import CrossConnect, CrossConnectAttachment

__all__ = ('CrossConnectAttachmentSerializer', 'CrossConnectSerializer')


class CrossConnectSerializer(NetBoxModelSerializer):
    status = ChoiceField(choices=CrossConnectStatusChoices, required=False)
    site = SiteSerializer(nested=True)
    tenant = TenantSerializer(nested=True)

    class Meta:
        model = CrossConnect
        fields = [
            'id', 'url', 'display_url', 'display', 'cross_connect_id', 'ritm', 'status', 'site', 'tenant',
            'activation_date', 'last_known_path', 'description', 'comments', 'tags', 'custom_fields', 'created',
            'last_updated',
        ]
        brief_fields = ('id', 'url', 'display', 'cross_connect_id', 'ritm', 'status', 'description')


class CrossConnectAttachmentSerializer(NetBoxModelSerializer):
    cross_connect = CrossConnectSerializer(nested=True)

    class Meta:
        model = CrossConnectAttachment
        fields = [
            'id', 'url', 'display_url', 'display', 'cross_connect', 'file', 'name', 'description', 'tags',
            'custom_fields', 'created', 'last_updated',
        ]
        brief_fields = ('id', 'url', 'display', 'name', 'description')
