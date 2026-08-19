import re
from email_validator import validate_email, EmailNotValidError

def is_valid_kenyan_phone(number):
    pattern = r'^(07|01)\d{8}$'
    return bool(re.match(pattern, number))

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False