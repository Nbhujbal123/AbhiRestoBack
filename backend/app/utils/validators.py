import re


def validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email.strip()) is not None


def validate_password(password: str):
    if not password or not isinstance(password, str):
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, None


def validate_phone(phone: str):
    if phone in [None, ""]:
        return True, None
    if not isinstance(phone, str):
        return False, "Invalid phone number"
    pattern = r"^\+?[\d\s-]{10,}$"
    if not re.match(pattern, phone.strip()):
        return False, "Invalid phone number format"
    return True, None


def validate_role(role: str) -> bool:
    return role in ["admin", "customer"]
