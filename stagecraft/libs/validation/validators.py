from django.core.validators import RegexValidator


slug_validator = RegexValidator(
    '^[-a-z0-9]+$',
    message='Slug can only contain lower case letters, numbers or hyphens'
)
