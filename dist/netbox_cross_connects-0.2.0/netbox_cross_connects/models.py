
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from netbox.models import NetBoxModel, PrimaryModel

from .choices import CrossConnectStatusChoices
from .validators import CrossConnectIDValidator

__all__ = ('CrossConnect', 'CrossConnectAttachment')


def cross_connect_attachment_upload_to(instance, filename):
    cross_connect_id = getattr(instance.cross_connect, 'cross_connect_id', 'unassigned')
    return f"cross-connect-attachments/{cross_connect_id}/{filename}"


class CrossConnect(PrimaryModel):
    cross_connect_id = models.CharField(
        verbose_name=_('cross connect ID'),
        max_length=100,
        unique=True,
        validators=(CrossConnectIDValidator,),
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
    provider = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='provided_cross_connects',
        verbose_name=_('provider'),
        blank=True,
        null=True,
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

    def clean(self):
        super().clean()
        if self._state.adding and not self.provider_id:
            raise ValidationError({
                'provider': _('Provider is required when creating a cross connect.'),
            })


class CrossConnectAttachment(NetBoxModel):
    cross_connect = models.ForeignKey(
        to='netbox_cross_connects.CrossConnect',
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('cross connect'),
    )
    file = models.FileField(
        verbose_name=_('file'),
        upload_to=cross_connect_attachment_upload_to,
    )
    name = models.CharField(
        verbose_name=_('name'),
        max_length=100,
        blank=True,
    )
    description = models.CharField(
        verbose_name=_('description'),
        max_length=200,
        blank=True,
    )

    class Meta:
        ordering = ('name', 'pk')
        verbose_name = _('cross connect attachment')
        verbose_name_plural = _('cross connect attachments')

    def __str__(self):
        return self.name or self.filename

    @property
    def filename(self):
        return Path(self.file.name).name if self.file else ''

    @property
    def size(self):
        return self.file.size if self.file else 0


@receiver(pre_save, sender=CrossConnectAttachment)
def delete_replaced_cross_connect_attachment_file(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if old_instance.file and old_instance.file.name != instance.file.name:
        old_instance.file.delete(save=False)


@receiver(post_delete, sender=CrossConnectAttachment)
def delete_cross_connect_attachment_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
