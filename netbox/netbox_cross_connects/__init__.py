from netbox.plugins import PluginConfig


class NetBoxCrossConnectsConfig(PluginConfig):
    name = 'netbox_cross_connects'
    verbose_name = 'NetBox Cross Connects'
    description = 'NetBox plugin for managing cross connects.'
    version = '0.1.0'
    base_url = 'cross-connects'
    min_version = '4.6.0'


config = NetBoxCrossConnectsConfig
