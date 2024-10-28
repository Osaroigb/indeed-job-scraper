import requests
from bs4 import BeautifulSoup
from database import get_session
from database.models import JobListing
from datetime import datetime, timezone
from config import logging, SCRAPER_API_KEY



def scrape_jobs_from_page(page_url, page_number, job_search_id):
    """
    Scrapes job details from a given page URL using ScraperAPI and stores each job in the JobListing table.
    """
    try:
        # Set up ScraperAPI endpoint and parameters
        api_url = "http://api.scraperapi.com"
        params = {
            'api_key': SCRAPER_API_KEY,
            'url': page_url
        }

        # Make request to ScraperAPI
        response = requests.get(api_url, params=params, timeout=3)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        job_listings = []

        # Find each job card element
        job_cards = soup.select('li.css-1ac2h1w')  # Each job is within a list element

        for job in job_cards:
            # Extract job title
            job_title_element = job.select_one('a.jcs-JobTitle')
            job_title = job_title_element.get_text(strip=True) if job_title_element else "N/A"

            # Extract company name
            company_element = job.select_one('span[data-testid="company-name"]')
            company = company_element.get_text(strip=True) if company_element else "N/A"

            # Extract job location
            location_element = job.select_one('div[data-testid="text-location"]')
            location = location_element.get_text(strip=True) if location_element else "N/A"

            # Extract posted date
            posted_date_element = job.select_one('span[data-testid="myJobsStateDate"]')
            posted_date = posted_date_element.get_text(strip=True).replace("Posted", "").strip() if posted_date_element else "N/A"

            # Extract job link
            job_link_element = job_title_element.get("href") if job_title_element else None
            job_link = f"https://uk.indeed.com{job_link_element}" if job_link_element else "N/A"

            # Append job data to list
            job_listings.append(JobListing(
                job_search_id=job_search_id,
                date_scraped=datetime.now(timezone.utc),
                page_number=page_number,
                job_title=job_title,
                company=company,
                location=location,
                posted_date=posted_date,
                job_link=job_link
            ))

        # Store job listings in the database
        with get_session() as session:
            session.add_all(job_listings)
            session.commit()

        logging.info(f"Scraped {len(job_listings)} jobs from page {page_number} for job search ID {job_search_id}")

    except Exception as e:
        logging.error(f"Failed to scrape jobs from page {page_number} for job search ID {job_search_id}: {e}")