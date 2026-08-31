from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

__all__ = ('CrossConnectIDValidator',)


CrossConnectIDValidator = RegexValidator(
    regex=r'^ID-[A-Z0-9]+-\d{5}$',
    message=_('Cross connect ID must match the format ID-<CODE>-<5 digits>.'),
    code='invalid',
)
