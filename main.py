import os
from database import engine, Base
from config import logging, validate_env
from jobs.job_cleaner import clean_job_titles
from jobs.link_generator import read_job_titles, store_generated_links


def main():
    validate_env()

    #? Define the input and output file names using absolute paths
    input_file = os.path.join(os.path.dirname(__file__), 'target_jobs.txt')
    output_file = os.path.join(os.path.dirname(__file__), 'cleaned_jobs.txt')

    # Run the job cleaner to create cleaned_jobs.txt
    clean_job_titles(input_file, output_file)
    
    # Initialize the database (create tables if they don't exist)
    Base.metadata.create_all(engine)
    
    # Read job titles from the cleaned_jobs.txt file
    job_file = os.path.join(os.path.dirname(__file__), 'cleaned_jobs.txt')
    job_titles = read_job_titles(job_file)
    
    # Store generated links in the database
    store_generated_links(job_titles)
    logging.info("Process completed: Job links generated and stored.")

if __name__ == "__main__":
    main()