import time
import requests
from database import get_session
from config import Config, logging
from database.models import JobSearch, JobListing
from concurrent.futures import ThreadPoolExecutor, as_completed
from jobs.job_scraper import scrape_jobs_from_page, scrape_job_details


# Use Config class to access ENVs
MAX_BOTS = Config.MAX_BOTS
RETRY_LIMIT = Config.RETRY_LIMIT


def process_job_search(job_search):
    """
    Process each job search by scraping paginated links and job details.
    Logs time taken, retry attempts, and error messages.
    """
    start_time = time.time()
    success = False

    with get_session() as session:
        for page_num, page_url in enumerate(job_search.pagination_links, start=1):
            retry_count = 0

            while retry_count < RETRY_LIMIT:
                try:
                    scrape_jobs_from_page(page_url, page_num, job_search.id)
                    logging.warning(f"Page {page_num} scraped successfully for {job_search.job_title}")

                    success = True
                    break
                except Exception as e:
                    retry_count += 1
                    
                    logging.warning(f"Retry {retry_count}/{RETRY_LIMIT} for page {page_num} of {job_search.job_title}")
                    time.sleep(2 ** retry_count)  # Exponential backoff

            if not success:
                logging.error(f"Failed to scrape page {page_num} for {job_search.job_title} after {RETRY_LIMIT} attempts")

    end_time = time.time()
    logging.warning(f"Completed job search for {job_search.job_title} in {end_time - start_time:.2f} seconds")


def process_job_listing_details(job_listing):
    """
    Process each job listing to scrape detailed job information.
    Logs time taken, retry attempts, and error messages.
    """
    start_time = time.time()
    success = False
    retry_count = 0

    while retry_count < RETRY_LIMIT:
        try:
            # Attempt to scrape job details
            scrape_job_details(job_listing)
            success = True
            logging.info(f"Successfully scraped details for job ID {job_listing.id}")
            break  # Exit loop if successful

        except requests.exceptions.Timeout:
            retry_count += 1
            logging.warning(f"Timeout error for job ID {job_listing.id}. Retry {retry_count}/{RETRY_LIMIT}.")
            time.sleep(2 ** retry_count)  # Exponential backoff for retries

        except requests.exceptions.RequestException as e:
            retry_count += 1
            logging.warning(f"Network error for job ID {job_listing.id}: {e}. Retry {retry_count}/{RETRY_LIMIT}.")
            time.sleep(2 ** retry_count)

        except Exception as e:
            # Log non-network-related errors without retries
            logging.error(f"Non-retryable error scraping details for job ID {job_listing.id}: {e}")
            break

    if not success:
        logging.error(f"Failed to scrape details for job ID {job_listing.id} after {RETRY_LIMIT} attempts")

    end_time = time.time()
    logging.info(f"Completed job details scraping for job ID {job_listing.id} in {end_time - start_time:.2f} seconds")


def run_bot_manager():
    """
    Run the bot manager to handle 80 concurrent bots for job searches and job details scraping.
    """
    logging.warning("Starting bot manager with concurrent scraping")

    # Phase 1: Process job searches (pagination links)
    with get_session() as session:
        job_searches = session.query(JobSearch).filter(JobSearch.pagination_links.isnot(None)).all()

    with ThreadPoolExecutor(max_workers=MAX_BOTS) as executor:
        futures = [executor.submit(process_job_search, job_search) for job_search in job_searches]
        
        # Collect results for job search phase
        for future in as_completed(futures):
            try:
                future.result()  # Raise exceptions if any
            except Exception as e:
                logging.error(f"Bot manager encountered an error in job search phase: {e}")

    logging.warning("Job search phase completed.")

    # Phase 2: Process job listing details after all paginated pages are scraped
    with get_session() as session:
        job_listings = session.query(JobListing).filter(JobListing.apply_now_link.is_(None)).all()

    with ThreadPoolExecutor(max_workers=MAX_BOTS) as executor:
        futures = [executor.submit(process_job_listing_details, job_listing) for job_listing in job_listings]

        # Collect results for job listing details phase
        for future in as_completed(futures):
            try:
                future.result()  # Raise exceptions if any
            except Exception as e:
                logging.error(f"Bot manager encountered an error in job listing details phase: {e}")

    logging.info("Job listing details phase completed.")
    logging.warning("Bot manager completed all tasks.")