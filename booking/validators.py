def validate_non_empty(text: str, field_name: str) -> bool:
    if not text or not text.strip():
        print(f"\n❌ {field_name} cannot be empty.")
        return False
    return True


def validate_min_length(text: str, min_len: int, field_name: str) -> bool:
    if len(text.strip()) < min_len:
        print(f"\n❌ {field_name} must be at least {min_len} characters.")
        return False
    return True


def validate_choice(choice: int, max_value: int, field_name: str) -> bool:
    if choice < 1 or choice > max_value:
        print(f"\n❌ Invalid {field_name} selection.")
        return False
    return True
