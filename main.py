import os
import subprocess 
from database import session, Base
from jobs.link_generator import read_job_titles, store_generated_links

def run_job_cleaner():
    """Run the job cleaner script to generate cleaned_jobs.txt."""
    job_cleaner_script = os.path.join(os.path.dirname(__file__), 'jobs', 'job_cleaner.py')
    subprocess.run(['python', job_cleaner_script], check=True)

def main():
    # Run the job cleaner to create cleaned_jobs.txt
    run_job_cleaner()
    
    # Initialize the database (create tables if they don't exist)
    Base.metadata.create_all(session.bind)  # Assuming you have a Base class defined in models.py
    
    # Read job titles from the cleaned_jobs.txt file
    job_file = os.path.join(os.path.dirname(__file__), 'cleaned_jobs.txt')
    job_titles = read_job_titles(job_file)
    
    # Store generated links in the database
    store_generated_links(job_titles)
    print("Process completed: Job links generated and stored.")

if __name__ == "__main__":
    main()