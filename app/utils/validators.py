import re


def is_valid_registration_number(registration_number: str) -> bool:
    """
    Checks if the registration number contains only digits
    and is between 8 and 15 characters long.
    """
    return bool(re.fullmatch(r"\d{8,15}", registration_number.strip()))