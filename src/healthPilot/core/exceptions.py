class AppError(Exception):
    """Domain error mapped to HTTP responses by exception handlers."""

    def __init__(self, message: str, code: str, status_code: int):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class AuthError(AppError):
    def __init__(self, message: str, code: str = "AUTH_ERROR", status_code: int = 401):
        super().__init__(message, code, status_code)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Admin access required", code: str = "FORBIDDEN"):
        super().__init__(message, code, 403)


class NotFoundError(AppError):
    def __init__(self, message: str, code: str = "NOT_FOUND"):
        super().__init__(message, code, 404)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "CONFLICT"):
        super().__init__(message, code, 409)


class SyncError(AppError):
    def __init__(self, message: str, code: str = "SYNC_ERROR"):
        super().__init__(message, code, 502)
