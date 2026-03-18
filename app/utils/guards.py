from app.utils.errors import InputTooLargeError


def enforce_max_length(field_name: str, value: str, max_length: int) -> None:
    if len(value) > max_length:
        raise InputTooLargeError(field_name, max_length=max_length, actual_length=len(value))
