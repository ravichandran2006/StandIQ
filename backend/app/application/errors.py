class ServiceError(Exception):
    status_code = 400
    code = "service_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ServiceError):
    status_code = 404
    code = "not_found"


class ConflictError(ServiceError):
    status_code = 409
    code = "conflict"
    
class DatabaseUnavailableError(ServiceError):
    status_code = 503
    code = "database_unavailable"