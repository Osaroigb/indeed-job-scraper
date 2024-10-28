import time
import logging
from database import get_session
from config import MAX_BOTS, RETRY_LIMIT
from database.models import JobSearch, JobListing
from concurrent.futures import ThreadPoolExecutor, as_completed
from jobs.job_scraper import scrape_jobs_from_page, scrape_job_details


def process_job_search(job_search):
    """
    Process each job search by scraping paginated links and job details.
    """
    with get_session() as session:
        for page_num, page_url in enumerate(job_search.pagination_links, start=1):
            retry_count = 0

            while retry_count < RETRY_LIMIT:
                try:
                    # Scrape each page for job listings
                    scrape_jobs_from_page(page_url, page_num, job_search.id)
                    break  # Break if successful

                except Exception as e:
                    logging.error(f"Error scraping page {page_num} for {job_search.job_title}: {e}")

                    retry_count += 1
                    time.sleep(2 ** retry_count)  # Exponential backoff


def process_job_listing_details(job_listing):
    """
    Process each job listing to scrape detailed job information.
    """
    retry_count = 0
    
    while retry_count < RETRY_LIMIT:
        try:
            # Scrape detailed job information from the job listing link
            scrape_job_details(job_listing)
            break  # Break if successful
        except Exception as e:
            logging.error(f"Error scraping details for job ID {job_listing.id}: {e}")

            retry_count += 1
            time.sleep(2 ** retry_count)  # Exponential backoff


def run_bot_manager():
    """
    Run the bot manager to handle 80 concurrent bots for job searches and job details scraping.
    """
    with get_session() as session:
        job_searches = session.query(JobSearch).filter(JobSearch.pagination_links.isnot(None)).all()
        job_listings = session.query(JobListing).filter(JobListing.apply_now_link.is_(None)).all()

    # Create thread pools for parallel job scraping and details scraping
    with ThreadPoolExecutor(max_workers=MAX_BOTS) as executor:
        futures = []

        # Submit job search tasks to the pool
        for job_search in job_searches:
            futures.append(executor.submit(process_job_search, job_search))

        # Submit job listing details tasks to the pool
        for job_listing in job_listings:
            futures.append(executor.submit(process_job_listing_details, job_listing))

        # Collect results
        for future in as_completed(futures):
            try:
                future.result()  # Raise exceptions if any
            except Exception as e:
                logging.error(f"Bot manager encountered an error: {e}")

    logging.info("Bot manager completed all tasks.")