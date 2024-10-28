import os
from database import engine, Base
from config import logging, validate_env
from bots.bot_manager import run_bot_manager
from jobs.job_cleaner import clean_job_titles
from scraper_utils.last_page_finder import store_last_pages
from jobs.link_generator import read_job_titles, store_generated_links, store_pagination_links


def main():
    validate_env()

    #? Define the input and output file names using absolute paths
    input_file = os.path.join(os.path.dirname(__file__), 'jobs/target_jobs.txt')
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


    # # Scrape job listings for each pagination link
    # with get_session() as session:
    #     job_searches = session.query(JobSearch).all()

    #     for job in job_searches:
    #         if job.pagination_links:

    #             for page_num, page_url in enumerate(job.pagination_links, start=1):
    #                 scrape_jobs_from_page(page_url, page_num, job.id)

    # logging.info("Job scraping completed for all paginated links.")


    # # Process individual job links for additional details
    # with get_session() as session:
    #     job_listings = session.query(JobListing).all()
        
    #     for listing in job_listings:
    #         if listing.job_link:
    #             scrape_job_details(listing)

    # logging.info("All job listings updated with detailed information.")

    # Run the bot manager to handle concurrent job scraping and detailed job information retrieval
    run_bot_manager()
    logging.info("scrape_jobs_from_page & scrape_job_details tasks completed by bot manager.")


if __name__ == "__main__":
    main()