import csv
from apollo.utils.concurrency_limiter import limit_concurrency
from apollo.services.fetch_people_data import fetch_apollo_people_data


def process_csv(input_file: str, output_file: str, headers: dict):
    """
    Processes a CSV file to fetch Apollo.io data for companies and save enriched data.

    :param input_file: str, Path to the input CSV file
    :param output_file: str, Path to save the output CSV file
    :param headers: dict, Request headers
    """
    with open(input_file, "r") as infile:
        reader = csv.DictReader(infile)
        companies = [row["Company"] for row in reader]

    enriched_data = limit_concurrency(
        companies,
        lambda company: fetch_apollo_people_data(
            company,
            {
                "person_locations": ["London, United Kingdom"],
                "contact_email_status": ["likely to engage"],
                # "person_titles": [
                #     "Compensation & Benefits", "Culture, Diversity & Inclusion", "HR Business Partner"
                # ],
                "person_titles": [
                    "Compensation & Benefits",
                    "Culture, Diversity & Inclusion",
                    "Employee & Labor Relations",
                    "Health & Safety",
                    "Human Resource Information System",
                    "Human Resources",
                    "HR Business Partner",
                    "Learning & Development",
                    "Organizational Development",
                    "Recruiting & Talent Acquisition",
                    "Talent Management",
                    "Workforce Management",
                    "People Operations",
                    "Recruitment",
                    "Talent",
                    "Recruiter",
                    "Equity and Inclusion",
                    "Talent Acquisition",
                    "Recruitment Lead",
                    "Recruiting",
                    "HR Business Advisor",
                    "Employee Relations Associate",
                    "HR Business Advisor"
                ],
                "departments": ["master human resources"],
                "page": 1,
                "per_page": 100,
                "q_keywords": company,
            },
            headers,
        ),
    )

    with open(output_file, "w", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=[
            "First Name", "Last Name", "Job Title", "Email", "Company", "LinkedIn URL"
        ])
        
        writer.writeheader()
        for data in enriched_data:
            writer.writerows(data)