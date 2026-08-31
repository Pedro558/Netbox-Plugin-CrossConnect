
from django.utils.translation import gettext as _

from netbox.plugins import PluginMenu
from netbox.plugins.navigation import PluginMenuButton, PluginMenuItem

menu = PluginMenu(
    label=_("Cross Connect"),
    icon_class="mdi mdi-swap-horizontal",
    groups=(
        (
            _("Cross Connects"),
            (
                PluginMenuItem(
                    link="plugins:netbox_cross_connects:crossconnect_list",
                    link_text=_("Cross Connects"),
                    permissions=["netbox_cross_connects.view_crossconnect"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:netbox_cross_connects:crossconnect_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["netbox_cross_connects.add_crossconnect"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:netbox_cross_connects:crossconnectattachment_list",
                    link_text=_("Attachments"),
                    permissions=["netbox_cross_connects.view_crossconnectattachment"],
                ),
            ),
        ),
    ),
)
