from database import get_session
from config import logging, Config
from database.models import JobSearch


BASE_URL = Config.BASE_URL


def read_job_titles(file_path):
    try:
        with open(file_path, 'r') as file:
            job_titles = [line.strip() for line in file if line.strip()]

        return job_titles
    except FileNotFoundError:
        logging.error(f"Error: The file {file_path} was not found.")
        return []
    

def generate_url(job_title, location="London"):
    formatted_title = job_title.replace(" ", "+")
    return f"{BASE_URL}/jobs?q={formatted_title}&l={location}"


def store_generated_links(job_titles):
    with get_session() as session:

        for title in job_titles:
            url = generate_url(title)
            job_entry = JobSearch(job_title=title, generated_link=url)

            try:
                session.add(job_entry)
            except Exception as e:
                logging.error(f"Error adding job entry for {title}: {e}")

        try:
            session.commit()
        except Exception as e:
            logging.error(f"Error committing to the database: {e}")


def generate_pagination_links(base_url, last_page):
    """
    Generate pagination links for all pages from 1 to last_page.
    """
    pagination_links = []

    for page_num in range(last_page):
        if page_num == 0:
            pagination_links.append(base_url)  # First page without "&start"
        else:
            pagination_links.append(f"{base_url}&start={page_num * 10}")

    return pagination_links


def store_pagination_links():
    """
    Retrieve each job search link and last page number, generate pagination links,
    and store them in the database.
    """
    with get_session() as session:
        job_searches = session.query(JobSearch).all()

        for job in job_searches:
            if job.last_page_number and job.last_page_number > 0:
                # Generate pagination links
                pagination_links = generate_pagination_links(job.generated_link, job.last_page_number)
                job.pagination_links = pagination_links

                logging.info(f"Pagination links generated for {job.job_title}")
            else:
                logging.warning(f"No pagination links generated for {job.job_title} (no results)")
                
        session.commit()