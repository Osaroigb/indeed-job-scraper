from database import session
from database.models import JobSearch


def read_job_titles(file_path):
    try:
        with open(file_path, 'r') as file:
            job_titles = [line.strip() for line in file if line.strip()]

        return job_titles
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return []
    

def generate_url(job_title, location="London"):
    formatted_title = job_title.replace(" ", "+")
    return f"https://uk.indeed.com/jobs?q={formatted_title}&l={location}"


def store_generated_links(job_titles):
    for title in job_titles:
        url = generate_url(title)
        job_entry = JobSearch(job_title=title, generated_link=url)
        
        try:
            session.add(job_entry)
        except Exception as e:
            print(f"Error adding job entry for {title}: {e}")
    
    try:
        session.commit()
    except Exception as e:
        print(f"Error committing to the database: {e}")