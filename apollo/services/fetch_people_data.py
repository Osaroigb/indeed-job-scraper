from config import Config, logging
from apollo.services.validate_payload import validate_payload
from apollo.utils.request_helper import make_request_with_retry


# Use Config class to access ENVs
APOLLO_API_URL = Config.APOLLO_API_URL


def fetch_apollo_people_data(company_name: str, payload: dict, headers: dict) -> list:
    """
    Fetches enriched people data from Apollo.io API.

    :param company_name: str, Company name for the search
    :param payload: dict, Request payload
    :param headers: dict, Request headers
    :return: list, List of enriched data
    """
    if not validate_payload(payload):
        raise ValueError(f"Invalid payload for company: {company_name}")

    page = 1
    enriched_data = []

    while True:
        try:
            payload["page"] = page
            data = make_request_with_retry(APOLLO_API_URL, headers, payload)

            if "contacts" in data:
                for contact in data["contacts"]:
                    enriched_data.append({
                        "First Name": contact.get("first_name", "N/A"),
                        "Last Name": contact.get("last_name", "N/A"),
                        "Job Title": contact.get("title", "N/A"),
                        "Email": contact.get("email", "N/A"),
                        "Company": contact.get("organization_name", "N/A"),
                        "LinkedIn URL": contact.get("linkedin_url", "N/A"),
                    })

            if page >= data.get("pagination", {}).get("total_pages", 0):
                break

            page += 1
        except Exception as e:
            print(f"Error fetching data for {company_name}: {e}")
            break

    return enriched_data
