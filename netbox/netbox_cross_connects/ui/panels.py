from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels


class CrossConnectPanel(panels.ObjectAttributesPanel):
    cross_connect_id = attrs.TextAttr(
        'cross_connect_id',
        label=_('Cross Connect ID'),
        style='font-monospace',
        copy_button=True,
    )
    ritm = attrs.TextAttr('ritm', label=_('RITM'), style='font-monospace', copy_button=True)
    status = attrs.ChoiceAttr('status')
    site = attrs.RelatedObjectAttr('site', linkify=True)
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True, grouped_by='group')
    activation_date = attrs.DateTimeAttr('activation_date', spec='date')
    description = attrs.TextAttr('description')
