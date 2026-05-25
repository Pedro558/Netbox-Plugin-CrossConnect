from django.utils.translation import gettext as _

from netbox.plugins.navigation import PluginMenuButton, PluginMenuItem

menu_items = (
    PluginMenuItem(
        link='plugins:netbox_cross_connects:crossconnect_list',
        link_text=_('Cross Connects'),
        buttons=(
            PluginMenuButton(
                link='plugins:netbox_cross_connects:crossconnect_add',
                title=_('Add'),
                icon_class='mdi mdi-plus-thick',
            ),
        ),
    ),
)
