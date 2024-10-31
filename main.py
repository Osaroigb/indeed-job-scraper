import os
import requests
from config import logging, Config
from database.models import JobSearch
from bots.bot_manager import run_bot_manager
from jobs.job_cleaner import clean_job_titles
from database import engine, Base, get_session
from scraper_utils.last_page_finder import store_last_pages
from jobs.link_generator import read_job_titles, store_generated_links, store_pagination_links


# Use Config class to access ENVs
BASE_URL = Config.BASE_URL
SCRAPER_API_KEY = Config.SCRAPER_API_KEY
SCRAPER_API_URL = Config.SCRAPER_API_URL


def scraper_api_health_check():
    """
    Checks if ScraperAPI is accessible. Terminates the script if unavailable.
    """
    params = {'api_key': SCRAPER_API_KEY, 'url': BASE_URL}

    try:
        response = requests.get(SCRAPER_API_URL, params=params, timeout=3)
        if response.status_code == 200:
            logging.info("ScraperAPI is reachable.")
            return True
        else:
            logging.error("ScraperAPI returned an unexpected status code.")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"ScraperAPI health check failed: {e}")
        return False
    

def log_performance_metrics():
    """
    Logs overall performance metrics of the scraper.
    """
    with get_session() as session:
        total_jobs = session.query(JobSearch).count()
        total_scraped = session.query(JobSearch).filter(JobSearch.last_page_number.isnot(None)).count()
        success_rate = (total_scraped / total_jobs) * 100 if total_jobs > 0 else 0

        logging.info(f"Total job titles: {total_jobs}")
        logging.warning(f"Successfully scraped: {total_scraped}")
        logging.info(f"Scraping success rate: {success_rate:.2f}%")


def main():
    # Run the ScraperAPI health check before proceeding
    if not scraper_api_health_check():
        logging.error("ScraperAPI is down or unreachable. Exiting script.")
        return  # Exit script if ScraperAPI is not accessible
    
    # Validate environment variables
    Config.validate_env()

    #? Define the input and output file names using absolute paths
    # input_file = os.path.join(os.path.dirname(__file__), 'jobs/target_jobs.txt')
    input_file = os.path.join(os.path.dirname(__file__), 'jobs/test_jobs.txt')
    output_file = os.path.join(os.path.dirname(__file__), 'jobs/cleaned_jobs.txt')

    # Run the job cleaner to create cleaned_jobs.txt
    clean_job_titles(input_file, output_file)

    # Initialize the database (create tables if they don't exist)
    Base.metadata.create_all(engine)

    # Read job titles from the cleaned_jobs.txt file
    job_titles = read_job_titles(output_file)

    logging.warning("job_titles length below!")
    logging.info(len(job_titles))
    
    # Store generated links in the database
    store_generated_links(job_titles)
    logging.info("Process completed: Job links generated and stored.")


    # Clean up the temporary cleaned_jobs.txt file
    try:
        os.remove(output_file)
        logging.info("cleaned_jobs file has been deleted.")
    except Exception as e:
        logging.warning(f"Failed to delete cleaned_jobs file: {e}")


    # Retrieve and store last page for each job link
    store_last_pages()

    # Generate and store pagination links for each job link
    store_pagination_links()
    logging.info("Pagination links for each job search stored in the database.")

    # Run the bot manager to handle concurrent job scraping and detailed job information retrieval
    run_bot_manager()
    
    # Log performance metrics after scraping
    log_performance_metrics()
    logging.warning("All tasks completed and performance metrics logged")


if __name__ == "__main__":
    main()