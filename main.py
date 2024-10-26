import os
from database.models import JobSearch
from config import logging, validate_env
from jobs.job_cleaner import clean_job_titles
from database import engine, Base, get_session
from scraper_utils.last_page_finder import get_last_page
from jobs.link_generator import read_job_titles, store_generated_links


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
    job_file = os.path.join(os.path.dirname(__file__), 'jobs/cleaned_jobs.txt')
    job_titles = read_job_titles(job_file)

    # logging.warning("job_titles length below!")
    # logging.info(len(job_titles))
    
    # Store generated links in the database
    store_generated_links(job_titles)
    logging.info("Process completed: Job links generated and stored.")

    try:
        # Delete the file
        os.remove(job_file)
        logging.warning(f"cleaned_jobs file has been deleted.")
    except FileNotFoundError:
        logging.warning(f"Error: The file '{job_file}' does not exist.")
    except PermissionError:
        logging.warning(f"Error: You do not have permission to delete '{job_file}'.")
    except Exception as e:
        logging.warning(f"An error occurred: {e}")

    # Initialize counter for job titles with no search results
    no_result_count = 0

    # Retrieve and store last page for each job link
    with get_session() as session:
        job_searches = session.query(JobSearch).all()

        for job in job_searches:
            last_page = get_last_page(job.generated_link)
            job.last_page_number = last_page

            # Increment counter if there are no results for this job title
            if last_page == 0:
                no_result_count += 1

        session.commit()
        
     # Log the count of job titles with no search results
    logging.info(f"Process completed: Last pages determined and stored for each job link.")
    logging.warning(f"Total job titles with no search results: {no_result_count}")


if __name__ == "__main__":
    main()