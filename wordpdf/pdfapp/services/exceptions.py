"""Service exceptions with safe frontend messages."""


class UserFacingError(Exception):
    """An error message that is safe to show to users."""


class FileValidationError(UserFacingError):
    """Uploaded file validation failed."""


class ConversionError(UserFacingError):
    """Document conversion failed after all supported fallbacks."""


def public_error_message(exc):
    if isinstance(exc, UserFacingError):
        return str(exc)
    return "We could not process this file. Please check the file and try again."
