import requests
from bs4 import BeautifulSoup
from database import get_session
from config import logging, Config
from database.models import JobListing
from datetime import datetime, timezone


# Use Config class to access ENVs
BASE_URL = Config.BASE_URL
SCRAPER_API_KEY = Config.SCRAPER_API_KEY
SCRAPER_API_URL = Config.SCRAPER_API_URL


def scrape_jobs_from_page(page_url, page_number, job_search_id):
    """
    Scrapes job details from a given page URL using ScraperAPI and stores each job in the JobListing table.
    """
    try:
        # Set up ScraperAPI endpoint and parameters
        payload = {
            'api_key': SCRAPER_API_KEY,
            'url': page_url
        }

        # Make request to ScraperAPI
        response = requests.get(SCRAPER_API_URL, params=payload, timeout=10)
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
            job_link = f"{BASE_URL}{job_link_element}" if job_link_element else "N/A"

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


def scrape_job_details(job_listing):
    """
    Visits an individual job link to scrape additional details like stars, job type,
    full job description, and apply now link. Retries if a timeout occurs.
    """
    try:
        # Construct the ScraperAPI request for the job link
        payload = {
            'api_key': SCRAPER_API_KEY,
            'url': job_listing.job_link
        }

        # Send request to ScraperAPI
        response = requests.get(SCRAPER_API_URL, params=payload, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the stars rating
        stars_element = soup.select_one('div.css-1unnuiz span')
        stars = stars_element.get_text(strip=True) if stars_element else "N/A"

        # Extract job location
        # location_element = soup.select_one('div[data-testid="job-location"]')
        # location = location_element.get_text(strip=True) if location_element else "N/A"
        
        # Extract the job type
        job_type_element = soup.select_one('div.js-match-insights-provider-g6kqeb .js-match-insights-provider-tvvxwd')
        job_type = job_type_element.get_text(strip=True) if job_type_element else "N/A"

        # Extract the full job description
        description_element = soup.select_one('#jobDescriptionText')
        full_description = description_element.get_text(strip=True) if description_element else "N/A"

        # Extract the "Apply Now" link
        apply_now_element = soup.select_one('button[contenthtml="Apply now"]')
        apply_now_link = apply_now_element['href'] if apply_now_element and apply_now_element.has_attr('href') else "N/A"

        if (apply_now_link == "N/A"):
            apply_now_fallback = soup.select_one('button#indeedApplyButton > span')
            apply_now_link = apply_now_fallback.get_text(strip=True)

        # Update job listing with new details
        with get_session() as session:
            listing = session.query(JobListing).filter_by(id=job_listing.id).first()
            listing.stars = stars
            # listing.location = location
            listing.job_type = job_type
            listing.full_description = full_description
            listing.apply_now_link = apply_now_link
            session.commit()

        logging.info(f"Detailed information scraped for job ID {job_listing.id}")

    except Exception as e:
        logging.error(f"Failed to scrape details for job ID {job_listing.id}: {e}")