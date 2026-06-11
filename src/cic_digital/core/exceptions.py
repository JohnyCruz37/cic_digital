class AppException(Exception):
    """Exceção base da aplicação."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class NotFoundError(AppException):
    status_code = 404
    code = "not_found"


class AppValidationError(AppException):
    status_code = 422
    code = "validation_error"


class UnauthorizedError(AppException):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppException):
    status_code = 403
    code = "forbidden"


class ServiceUnavailableError(AppException):
    status_code = 503
    code = "service_unavailable"
