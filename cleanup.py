import os
import csv
import requests
from database import get_session
from sqlalchemy import func, desc
from config import Config, logging
from datetime import datetime, timezone
from database.models import JobListing, JobSearch


# Use Config class to access ENVs
APOLLO_API_KEY = Config.APOLLO_API_KEY
APOLLO_API_URL = Config.APOLLO_API_URL


def remove_zero_page_records(input_file, output_file):
    """
    Reads a CSV file and removes rows where the page count is zero.
    Writes the filtered records to a new CSV file.
    
    Parameters:
    - input_file: str, the path to the CSV file to read
    - output_file: str, the path to save the filtered CSV file
    """
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # Write the header row to the output file
            headers = next(reader)
            writer.writerow(headers)

            # Filter out rows where the page count is 0
            removed_count = 0
            
            for row in reader:
                page_count = row[3]  # Assuming the page count is in the fourth column (index 3)
                if page_count.isdigit() and int(page_count) > 0:
                    writer.writerow(row)
                else:
                    removed_count += 1

            logging.info(f"Filtered out {removed_count} records with 0 pages from {input_file}.")

    except Exception as e:
        logging.error(f"Error processing CSV file: {e}")


def delete_zero_page_records():
    """
    Deletes all records from the JobSearch table where the last_page_number is 0.
    Logs the number of records deleted.
    """
    with get_session() as session:
        # Query to find all job search records with last_page_number = 0
        zero_page_records = session.query(JobSearch).filter(JobSearch.last_page_number == 0).all()
        
        # Count records to delete
        record_count = len(zero_page_records)
        
        if record_count > 0:
            for record in zero_page_records:
                session.delete(record)

            session.commit()
            logging.info(f"Deleted {record_count} records with last_page_number = 0 from JobSearch table.")
            
        else:
            logging.info("No records found with last_page_number = 0 in JobSearch table.")


def remove_na_job_titles():
    """
    Deletes all records from the JobListing table where job_title is 'N/A'.
    Logs the number of records deleted.
    """
    with get_session() as session:
        # Query to find all job listings with job_title = 'N/A'
        na_job_listings = session.query(JobListing).filter(JobListing.job_title == 'N/A').all()
        
        # Count records to delete
        record_count = len(na_job_listings)
        
        if record_count > 0:
            for record in na_job_listings:
                session.delete(record)
            session.commit()
            logging.info(f"Deleted {record_count} records with job_title = 'N/A' from JobListing table.")
        else:
            logging.info("No records found with job_title = 'N/A' in JobListing table.")


def count_unique_companies():
    """
    Counts the total number of unique company names in the JobListing table.
    Logs the total count of unique companies.
    """
    with get_session() as session:
        # Get the count of unique company names
        unique_companies_count = session.query(JobListing.company).distinct().count()
        
        logging.info(f"Total number of unique companies: {unique_companies_count}")
        return unique_companies_count


def upload_job_listings_from_csv(csv_file):
    """
    Reads entries from a CSV file and inserts them into the JobListing table.
    
    Parameters:
    - csv_file: str, the path to the CSV file to read
    """
    try:
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            job_listings = []
            for row in reader:
                job_listings.append(JobListing(
                    job_search_id=int(row['job_search_id']),
                    date_scraped=datetime.now(timezone.utc),
                    page_number=int(row['page_number']),
                    job_title=row['job_title'],
                    company=row['company'],
                    location=row['location'],
                    posted_date=row['posted_date'],
                    job_link=row['job_link'],
                    stars=row['stars'] if row['stars'] else None,
                    job_type=row['job_type'] if row['job_type'] else None,
                    full_description=row['full_description'] if row['full_description'] else None,
                    apply_now_link=row['apply_now_link'] if row['apply_now_link'] else None
                ))

        # Insert the job listings into the database
        with get_session() as session:
            session.bulk_save_objects(job_listings)
            session.commit()
            logging.info(f"Uploaded {len(job_listings)} job listings from {csv_file} into the database.")

    except Exception as e:
        logging.error(f"Error uploading job listings from CSV: {e}")


def export_non_null_apply_links_to_csv(output_file):
    """
    Counts and exports all records in the JobListing table where apply_now_link is NOT null.
    Saves the results to a CSV file.

    Parameters:
    - output_file: str, the path to save the CSV file.
    """
    try:
        with get_session() as session:
            # Query to find all job listings where apply_now_link is not null
            # job_listings = session.query(JobListing).filter(JobListing.apply_now_link.isnot(None)).all()

            # Query to find the first 100 job listings where apply_now_link is not null
            job_listings = (
                session.query(JobListing)
                .filter(JobListing.apply_now_link.isnot(None))
                .limit(100)
                .all()
            )

            # Count the total number of records
            record_count = len(job_listings)
            logging.info(f"Total job listings with apply_now_link not null: {record_count}")

            # Export records to a CSV file
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write the header
                writer.writerow(['ID', 'Job Title', 'Company', 'Location', 'Posted Date', 
                                 'Job Link', 'Stars', 'Job Type', 'Full Description', 'Apply Now Link'])

                # Write each job listing to the CSV
                for job in job_listings:
                    writer.writerow([
                        job.id,
                        job.job_title,
                        job.company,
                        job.location,
                        job.posted_date,
                        job.job_link,
                        job.stars,
                        job.job_type,
                        job.full_description,
                        job.apply_now_link
                    ])

            logging.info(f"Exported {record_count} job listings to {output_file}")

    except Exception as e:
        logging.error(f"Error exporting job listings to CSV: {e}")


def export_job_count_by_company(output_file):
    """
    Generates a CSV file that lists companies and their corresponding job counts, 
    ordered in descending order of job listings.

    Parameters:
    - output_file: str, the path to save the CSV file.
    """
    try:
        with get_session() as session:
            # Query to count jobs per company and order by count in descending order
            job_counts = (
                session.query(JobListing.company, func.count(JobListing.id).label("job_count"))
                .group_by(JobListing.company)
                .order_by(desc("job_count"))
                .all()
            )

            # Export the results to a CSV file
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write the header
                writer.writerow(["Company", "Job Count"])

                # Write each company's job count to the CSV
                for company, job_count in job_counts:
                    writer.writerow([company, job_count])

            logging.info(f"Exported job counts by company to {output_file}")

    except Exception as e:
        logging.error(f"Error exporting job counts by company to CSV: {e}")


def fetch_apollo_data(input_file, output_file):
    """
    Fetches enriched people data from Apollo.io API based on provided company names.
    Saves the results to a CSV file.

    Parameters:
    - input_file: str, path to the input CSV file with companies.
    - output_file: str, path to save the enriched data CSV file.
    """
    headers = {
        "x-api-key": APOLLO_API_KEY,
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json"
    }

    person_titles = [
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
    ]

    enriched_data = []
    has_errors = False
    
    try:
        # Read the input file
        with open(input_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                company_name = row['Company']
                logging.info(f"Fetching data for company: {company_name}")
                
                # Apollo.io API request payload
                payload = {
                    "person_locations": ["London, United Kingdom"],
                    "contact_email_status": ["likely to engage"],
                    "person_titles": person_titles,
                    # "job_functions": ["human resources"],  # Assuming job_functions filter supports HR roles
                    # "departments": ["master human resources"],
                    "page": 1,
                    "per_page": 100,
                    "q_keywords": company_name
                }

                # Add company name to the payload
                # payload["q_keywords"] = company_name

                while True:
                    try:
                        # Make the API request
                        response = requests.post(APOLLO_API_URL, headers=headers, json=payload)
                        response.raise_for_status()

                        # Parse response
                        data = response.json()

                        logging.warning('response data below!')
                        # logging.info(data)

                        # Check for contacts in the response
                        if "contacts" in data and data["contacts"]:

                            for contact in data["contacts"]:
                                enriched_data.append({
                                    "First Name": contact.get("first_name", "N/A"),
                                    "Last Name": contact.get("last_name", "N/A"),
                                    "Job Title": contact.get("title", "N/A"),
                                    "Email": contact.get("email", "N/A"),
                                    "Company": contact.get("organization_name", "N/A"),
                                    "LinkedIn URL": contact.get("linkedin_url", "N/A")
                                })

                        # Check if there are more pages
                        if data.get("pagination", {}).get("page") < data.get("pagination", {}).get("total_pages", 0):
                            payload["page"] += 1
                        else:
                            break


                    except requests.exceptions.RequestException as e:
                        logging.error(f"Request error for company {company_name}: {e}")
                        has_errors = True
                        break


    except Exception as e:
        logging.error(f"Error during data enrichment: {e}")
        has_errors = True


    # Save enriched data to CSV if no errors occurred
    if not has_errors and enriched_data:
        # Save enriched data to CSV
        try:
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=[
                    "First Name", "Last Name", "Job Title", "Email", "Company", "LinkedIn URL"
                ])

                writer.writeheader()
                writer.writerows(enriched_data)

            logging.info(f"Enriched data successfully saved to {output_file}")

        except Exception as e:
            logging.error(f"Error saving enriched data to CSV: {e}")

    else:
        logging.warning("No data was written to the CSV due to errors.")


def fetch_apollo_people_data(input_file: str, output_file: str):
    """
    Fetches enriched people data from Apollo.io API based on provided company names.
    Saves the results to a CSV file.

    Parameters:
    - input_file: str, path to the input CSV file with companies.
    - output_file: str, path to save the enriched data CSV file.
    """
    # Job titles and industries based on the provided documentation
    person_titles = [
        "Human Resources Manager", "Human Resources", "Human Resources Generalist", "HR Manager",
        "HR", "HR Assistant", "HR Officer", "HR Coordinator", "HR Administrator", "HR Executive",
        "Compensation & Benefits", "Culture, Diversity & Inclusion", "Employee & Labor Relations",
        "Health & Safety", "Human Resource Information System", "Learning & Development",
        "Organizational Development", "Recruiting & Talent Acquisition", "Talent Management",
        "Workforce Management", "People Operations"
    ]

    # industries = ["computer software", "information technology and services"]
    # num_employees = "1,10;11,20;21,50;51,100;101,200;201,500;501,1000;10001+;5001,10000;2001,5000;1001,2000"
    # revenue_range_min = 100000
    # revenue_range_max = 1000000

    enriched_data = []

    try:
        # Read the input file
        with open(input_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                company_name = row.get("Company")
                logging.info(f"Fetching data for company: {company_name}")

                # Initialize payload for the API request
                payload = {
                    # "numEmployees": num_employees,
                    "qKeywords": company_name,
                    "locations": "London, United Kingdom",
                    "apiKey": APOLLO_API_KEY,
                    "personTitle": ";".join(person_titles),
                    # "industry": ";".join(industries),
                    # "revenueRangeMin": revenue_range_min,
                    # "revenueRangeMax": revenue_range_max,
                    "next": ""  # Start with an empty pagination token
                }

                while True:
                    try:
                        # Make the API request
                        response = requests.get(APOLLO_API_URL, params=payload)
                        response.raise_for_status()
                        data = response.json()

                        logging.info(f"Data retrieved for company: {company_name}")

                        # Process the "people" section in the response
                        if "people" in data:
                            for person in data["people"]:
                                enriched_data.append({
                                    "First Name": person.get("firstName", "N/A"),
                                    "Last Name": person.get("lastName", "N/A"),
                                    "Job Title": person.get("title", "N/A"),
                                    "Email": person.get("email", "N/A"),
                                    "Company": person.get("organizationName", "N/A"),
                                    "LinkedIn URL": person.get("linkedinUrl", "N/A")
                                })

                        # Handle pagination
                        next_token = data.get("next", "")
                        if not next_token:
                            break  # Exit the loop if there's no next page
                        payload["next"] = next_token

                    except requests.exceptions.RequestException as e:
                        logging.error(f"Request error for company {company_name}: {e}")
                        break

    except Exception as e:
        logging.error(f"Error during data enrichment: {e}")

    # Write to CSV if data was successfully enriched
    if enriched_data:
        try:
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=[
                    "First Name", "Last Name", "Job Title", "Email", "Company", "LinkedIn URL"
                ])
                writer.writeheader()
                writer.writerows(enriched_data)

            logging.info(f"Enriched data successfully saved to {output_file}")
        except Exception as e:
            logging.error(f"Error saving enriched data to CSV: {e}")
    else:
        logging.warning("No data was written to the CSV due to errors or no results found.")


# Example usage
if __name__ == "__main__":
    # input_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/JobSearch.csv')
    # output_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/CleanedJobSearch.csv')

    # job_listing_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/JobListing.csv')
    # cleaned_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/CleanedJobListing.csv')

    # output_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/FilteredJobListings.csv')
    # output_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/100JobListings.csv')

    #? Run the function to clean the CSV file
    # remove_zero_page_records(input_csv_file, output_csv_file)

    #* Run the cleanup for job search records with last_page_number = 0
    # delete_zero_page_records()

    #! Remove job listings with "N/A" job titles
    # remove_na_job_titles()

    # export_non_null_apply_links_to_csv(output_csv_file)

    # TODO Count and log the total number of unique companies
    # count_unique_companies()

    #* Upload cleaned job listings to the database
    # upload_job_listings_from_csv(job_listing_csv_file)

    # output_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/JobCountByCompany.csv')
    # export_job_count_by_company(output_csv_file)

    # input_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/JobCountByCompany.csv')
    output_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/EmployeeData.csv')

    input_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/test.csv')
    # output_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/TestData.csv')
    fetch_apollo_data(input_csv_file, output_csv_file)