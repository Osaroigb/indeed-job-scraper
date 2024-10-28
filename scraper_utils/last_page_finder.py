import time
import random
import requests
from bs4 import BeautifulSoup
from database import get_session
from database.models import JobSearch
from config import logging, SCRAPER_API_KEY, SCRAPER_API_URL


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    # Add more User-Agents if needed
]
    

def get_last_page(search_url):
    """
    Retrieves the last page number for a job search URL, accounting for cases with no results.
    """
    try:
        # Introduce a delay before making the request to mimic human-like behavior
        time.sleep(random.uniform(1, 3))

        # Append start=3000 to navigate to the last page
        last_page_url = f"{search_url}&start=3000"

        headers = {
            "Accept": "text/html",
            "User-Agent": random.choice(USER_AGENTS)
        }

        # Make a direct request to Indeed's last page URL
        response = requests.get(last_page_url, headers=headers, timeout=3)
        response.raise_for_status()  # Raise an error if the request fails

        # Parse HTML and extract the last page number or check for no results
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for "no results" message
        no_results_message = soup.select_one(".jobsearch-NoResult-messageContainer")

        if no_results_message:
            logging.info(f"No results found for {search_url}")
            return 0  # Indicates that no pages are available for this search

          # Locate the pagination container and extract the last page number
        current_page = soup.select_one('a[data-testid="pagination-page-current"]')
        
        # Retrieve and convert the last page number if found
        if current_page and current_page.get_text().isdigit():
            last_page = int(current_page.get_text())
        else:
            last_page = 1  # Default to 1 if pagination is not found or accessible
        
        logging.info(f"Last page for {search_url} is {last_page}")
        return last_page

    except Exception as e:
        logging.error(f"Failed to retrieve last page for {search_url}: {e}")
        return 1


def get_last_page_with_scraper(search_url):
    """
    Retrieves the last page number for a job search URL using ScraperAPI,
    accounting for cases with no results.
    """
    try:
        # Append start=3000 to navigate to the last page
        last_page_url = f"{search_url}&start=3000"

        # ScraperAPI endpoint and parameters
        params = {
            'api_key': SCRAPER_API_KEY,
            'url': last_page_url
        }

        # Make a request to ScraperAPI
        response = requests.get(SCRAPER_API_URL, params=params, timeout=3)
        response.raise_for_status()  # Raise an error if the request fails

        # Parse HTML and extract the last page number or check for no results
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for "no results" message
        no_results_message = soup.select_one(".jobsearch-NoResult-messageContainer")
        if no_results_message:
            logging.info(f"No results found for {search_url}")
            return 0  # Indicates that no pages are available for this search

        # Locate the pagination container and extract the last page number
        current_page = soup.select_one('a[data-testid="pagination-page-current"]')
        
        # Retrieve and convert the last page number if found
        if current_page and current_page.get_text().isdigit():
            last_page = int(current_page.get_text())
        else:
            last_page = 1  # Default to 1 if pagination is not found or accessible
        
        logging.info(f"Last page for {search_url} is {last_page}")
        return last_page

    except Exception as e:
        logging.error(f"Failed to retrieve last page for {search_url}: {e}")
        return 1
    

def store_last_pages():
    """
    Retrieve and store the last page for each job search link.
    Count job titles with no search results.
    """
    no_result_count = 0  # Initialize counter for job titles with no search results

    with get_session() as session:
        job_searches = session.query(JobSearch).all()

        for job in job_searches:
            last_page = get_last_page_with_scraper(job.generated_link)
            job.last_page_number = last_page

            # Increment counter if there are no results for this job title
            if last_page == 0:
                no_result_count += 1
                logging.warning(f"No results for {job.job_title}")

        session.commit()

    # Log the count of job titles with no search results
    logging.info(f"Process completed: Last pages determined and stored for each job link.")
    logging.warning(f"Total job titles with no search results: {no_result_count}")