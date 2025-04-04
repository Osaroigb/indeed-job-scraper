from typing import TypedDict


class EnrichedData(TypedDict):
    first_name: str
    last_name: str
    job_title: str
    email: str
    company: str
    linkedIn_url: str


class ApolloPayload(TypedDict):
    person_locations: list
    contact_email_status: list
    person_titles: list
    departments: list
    page: int
    per_page: int
    q_keywords: str