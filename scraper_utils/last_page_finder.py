import requests
from bs4 import BeautifulSoup
from config import logging, Config


# Use Config class to access ENVs
SCRAPER_API_KEY = Config.SCRAPER_API_KEY
SCRAPER_API_URL = Config.SCRAPER_API_URL


def get_last_page(search_url):
    """
    Retrieves the last page number for a job search URL using ScraperAPI,
    accounting for cases with no results.
    """
    try:
        # Append start=3000 to navigate to the last page
        last_page_url = f"{search_url}&start=3000"

        # ScraperAPI endpoint and parameters
        payload = {
            'api_key': SCRAPER_API_KEY,
            'url': last_page_url,
            # 'country': 'GB'
        }

        # Make a request to ScraperAPI
        response = requests.get(SCRAPER_API_URL, params=payload, timeout=30)
        response.raise_for_status()  # Raise an error if the request fails

        # Parse HTML and extract the last page number or check for no results
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for "no results" message
        no_results_message = soup.select_one(".jobsearch-NoResult-messageContainer")
        if no_results_message:
            logging.info(f"No search results found for {search_url}")
            return 0  # Indicates that no pages are available for this search

        # Locate the pagination container and extract the last page number
        current_page = soup.select_one('a[data-testid="pagination-page-current"]')

        logging.warning("current_page below!")
        logging.info(current_page)
        
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