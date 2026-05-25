from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from netbox.models import PrimaryModel

from .choices import CrossConnectStatusChoices

__all__ = ('CrossConnect',)


class CrossConnect(PrimaryModel):
    cross_connect_id = models.CharField(
        verbose_name=_('cross connect ID'),
        max_length=100,
        unique=True,
        validators=(
            RegexValidator(
                regex=r'^ID-[A-Z0-9]+-\d{5}$',
                message=_('Cross connect ID must match the format ID-<CODE>-<5 digits>.'),
            ),
        ),
    )
    ritm = models.CharField(
        verbose_name=_('RITM'),
        max_length=11,
        validators=(
            RegexValidator(
                regex=r'^RITM\d{7}$',
                message=_('RITM must match the format RITM#######.'),
            ),
        ),
    )
    status = models.CharField(
        verbose_name=_('status'),
        max_length=50,
        choices=CrossConnectStatusChoices,
        default=CrossConnectStatusChoices.STATUS_ACTIVE,
    )
    site = models.ForeignKey(
        to='dcim.Site',
        on_delete=models.PROTECT,
        related_name='cross_connects',
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='cross_connects',
    )
    activation_date = models.DateField(
        verbose_name=_('activation date'),
        blank=True,
        null=True,
    )
    last_known_path = models.TextField(
        verbose_name=_('last known path'),
        blank=True,
    )

    class Meta:
        ordering = ('cross_connect_id',)
        verbose_name = _('cross connect')
        verbose_name_plural = _('cross connects')

    def __str__(self):
        return self.cross_connect_id

    def get_status_color(self):
        return CrossConnectStatusChoices.colors.get(self.status)
