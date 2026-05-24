from django.utils.translation import gettext_lazy as _

from utilities.choices import ChoiceSet

__all__ = ('CrossConnectStatusChoices',)


class CrossConnectStatusChoices(ChoiceSet):
    key = 'CrossConnect.status'

    STATUS_PLANNED = 'planned'
    STATUS_ACTIVE = 'active'
    STATUS_OFFLINE = 'offline'
    STATUS_DECOMMISSIONING = 'decommissioning'
    #STATUS_DECOMMISSIONED = 'decommissioned'

    CHOICES = (
        (STATUS_PLANNED, _('Planned'), 'cyan'),
        (STATUS_ACTIVE, _('Active'), 'green'),
        (STATUS_OFFLINE, _('Offline'), 'red'),
        (STATUS_DECOMMISSIONING, _('Decommissioning'), 'yellow'),
        #(STATUS_DECOMMISSIONED, _('Decommissioned'), 'gray'),
    )
