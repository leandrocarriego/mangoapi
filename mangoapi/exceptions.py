# mangoapi/exceptions.py


class MangoAPIError(Exception):
    def __init__(self, message: str = "An unexpected error occurred in MangoAPI"):
        super().__init__(message)


class SerializationError(MangoAPIError):
    def __init__(self, message: str = "Failed to serialize response data"):
        super().__init__(message)


class ValidationTypeError(MangoAPIError):
    def __init__(
        self, message: str = "Return value does not match the declared annotation"
    ):
        super().__init__(message)


class RequestParsingError(MangoAPIError):
    def __init__(self, message: str = "Failed to parse request parameters"):
        super().__init__(message)


class ViewExecutionError(MangoAPIError):
    def __init__(self, message: str = "Failed to execute view function"):
        super().__init__(message)
