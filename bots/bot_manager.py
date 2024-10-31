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
                    logging.info(f"Page {page_num} scraped successfully for {job_search.job_title}")

                    success = True
                    break
                except Exception as e:
                    retry_count += 1
                    
                    logging.warning(f"Retry {retry_count}/{RETRY_LIMIT} for page {page_num} of {job_search.job_title}")
                    time.sleep(2 ** retry_count)  # Exponential backoff

            if not success:
                logging.error(f"Failed to scrape page {page_num} for {job_search.job_title} after {RETRY_LIMIT} attempts")

    end_time = time.time()
    logging.info(f"Completed job search for {job_search.job_title} in {end_time - start_time:.2f} seconds")


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
    logging.info("Starting bot manager with concurrent scraping")

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