import time
import requests
from database import get_session
from config import Config, logging
from database.models import JobSearch, JobListing
from scraper_utils.last_page_finder import get_last_page
from concurrent.futures import ThreadPoolExecutor, as_completed
from jobs.job_scraper import scrape_jobs_from_page, scrape_job_details


# Use Config class to access ENVs
MAX_BOTS = Config.MAX_BOTS
RETRY_LIMIT = Config.RETRY_LIMIT
TIMEOUT_URLS_FILE = Config.TIMEOUT_URLS_FILE


def process_last_page(job_search):
    """
    Retrieve and update the last page number for a given job search.
    Includes a retry mechanism with exponential backoff and logs the time taken.
    If the last page retrieval fails due to a timeout, store the URL in a text file.
    """
    start_time = time.time()
    success = False
    retry_count = 0
    last_page_url = f"{job_search.generated_link}&start=3000"  # Construct the last page URL

    while retry_count < RETRY_LIMIT:
        try:
            # Attempt to retrieve the last page
            last_page = get_last_page(job_search.generated_link)
            
            with get_session() as session:
                job = session.query(JobSearch).filter_by(id=job_search.id).first()
                job.last_page_number = last_page
                session.commit()

            success = True
            break  # Exit loop if successful

        except requests.exceptions.Timeout:
            retry_count += 1
            logging.warning(f"Timeout error retrieving last page for {job_search.job_title}. Retry {retry_count}/{RETRY_LIMIT}.")
            time.sleep(2 ** retry_count)  # Exponential backoff for retries

        except Exception as e:
            retry_count += 1
            logging.warning(f"Error retrieving last page for {job_search.job_title}. Retry {retry_count}/{RETRY_LIMIT}.")
            time.sleep(2 ** retry_count)  # Exponential backoff for retries

    if not success:
        logging.error(f"Failed to determine last page for {job_search.job_title} after {RETRY_LIMIT} attempts")

        # Store the URL in a file for later retry
        with open(TIMEOUT_URLS_FILE, "a") as f:
            f.write(f"{last_page_url}\n")
        logging.info(f"Stored timeout URL for {job_search.job_title} in {TIMEOUT_URLS_FILE}")

    end_time = time.time()
    logging.info(f"Completed last page retrieval for {job_search.job_title} in {end_time - start_time:.2f} seconds")


def process_job_search(job_search):
    """
    Process each job search by scraping paginated links and job details.
    Logs time taken, retry attempts, and error messages.
    """
    start_time = time.time()
    success = False

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


def run_bot_manager(phase: str):
    """
    Run the bot manager to handle concurrent tasks for retrieving last pages, 
    job searches, and job listing details scraping.
    """
    logging.warning("Starting bot manager with concurrent scraping")

    if phase == "last_page":

        #? Phase 1: Retrieve last page for each job search
        with get_session() as session:
            job_searches = session.query(JobSearch).all()

        with ThreadPoolExecutor(max_workers=MAX_BOTS) as executor:
            futures = [executor.submit(process_last_page, job_search) for job_search in job_searches]

            # Collect results for last page retrieval phase
            for future in as_completed(futures):
                try:
                    future.result()  # Raise exceptions if any
                except Exception as e:
                    logging.error(f"Bot manager encountered an error in last page retrieval phase: {e}")

        logging.warning("Last page retrieval phase completed.")

    elif phase == "job_search_scraping":

        #? Phase 2: Process job searches (pagination links)
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


    elif phase == "job_listing_scraping":

        #? Phase 3: Process job listing details after all paginated pages are scraped
        with get_session() as session:
            job_listings = session.query(JobListing).all()

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