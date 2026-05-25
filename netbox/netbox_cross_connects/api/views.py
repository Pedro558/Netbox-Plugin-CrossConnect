from netbox.api.viewsets import NetBoxModelViewSet

from netbox_cross_connects import filtersets
from netbox_cross_connects.api import serializers
from netbox_cross_connects.models import CrossConnect

__all__ = ('CrossConnectViewSet',)


class CrossConnectViewSet(NetBoxModelViewSet):
    queryset = CrossConnect.objects.all()
    serializer_class = serializers.CrossConnectSerializer
    filterset_class = filtersets.CrossConnectFilterSet
