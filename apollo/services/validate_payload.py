def validate_payload(payload: dict) -> bool:
    """
    Validates the payload for Apollo API requests.

    :param payload: dict, The payload object to validate
    :return: bool, True if valid, otherwise False
    """
    required_fields = ["person_locations", "contact_email_status", "person_titles", "departments"]
    
    for field in required_fields:
        if field not in payload or not isinstance(payload[field], list):
            return False

    return True