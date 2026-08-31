from pathlib import Path
from warnings import catch_warnings, simplefilter

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from PIL import Image, UnidentifiedImageError

__all__ = (
    'CrossConnectIDValidator',
    'validate_cross_connect_attachment_file',
)

MAX_CROSS_CONNECT_ATTACHMENT_SIZE = 25 * 1024 * 1024
ALLOWED_CROSS_CONNECT_ATTACHMENT_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
IMAGE_FORMATS_BY_EXTENSION = {
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.png': 'PNG',
}


CrossConnectIDValidator = RegexValidator(
    regex=r'^ID-[A-Z0-9]+-\d{5}$',
    message=_('Cross connect ID must match the format ID-<CODE>-<5 digits>.'),
    code='invalid',
)


def validate_cross_connect_attachment_file(upload):
    """Validate the size, extension, and recognizable content of an attachment."""
    if not upload:
        return

    if upload.size > MAX_CROSS_CONNECT_ATTACHMENT_SIZE:
        raise ValidationError(
            _('Attachment files must not exceed 25 MB.'),
            code='attachment_file_too_large',
        )

    extension = Path(upload.name).suffix.lower()
    if extension not in ALLOWED_CROSS_CONNECT_ATTACHMENT_EXTENSIONS:
        raise ValidationError(
            _('Only PDF, JPG, JPEG, and PNG files are allowed.'),
            code='attachment_file_type_not_allowed',
        )

    try:
        upload.seek(0)

        if extension == '.pdf':
            if upload.read(5) != b'%PDF-':
                raise ValidationError(
                    _('The uploaded file is not a valid PDF.'),
                    code='attachment_file_content_invalid',
                )
            return

        with catch_warnings():
            simplefilter('error', Image.DecompressionBombWarning)
            image = Image.open(upload)
            image.verify()

        if image.format != IMAGE_FORMATS_BY_EXTENSION[extension]:
            raise ValidationError(
                _('The file content does not match its extension.'),
                code='attachment_file_content_invalid',
            )
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, SyntaxError):
        raise ValidationError(
            _('The uploaded file is not a valid %(file_type)s image.'),
            code='attachment_file_content_invalid',
            params={'file_type': extension.lstrip('.').upper()},
        )
    finally:
        upload.seek(0)
