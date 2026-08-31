
from netbox.api.viewsets import NetBoxModelViewSet

from netbox_cross_connects import filtersets
from netbox_cross_connects.api import serializers
from netbox_cross_connects.models import CrossConnect, CrossConnectAttachment

__all__ = ('CrossConnectAttachmentViewSet', 'CrossConnectViewSet')


class CrossConnectViewSet(NetBoxModelViewSet):
    queryset = CrossConnect.objects.all()
    serializer_class = serializers.CrossConnectSerializer
    filterset_class = filtersets.CrossConnectFilterSet


class CrossConnectAttachmentViewSet(NetBoxModelViewSet):
    queryset = CrossConnectAttachment.objects.select_related('cross_connect')
    serializer_class = serializers.CrossConnectAttachmentSerializer
