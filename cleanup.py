import os
import csv
from config import logging
from database import get_session
from database.models import JobSearch


def remove_zero_page_records(input_file, output_file):
    """
    Reads a CSV file and removes rows where the page count is zero.
    Writes the filtered records to a new CSV file.
    
    Parameters:
    - input_file: str, the path to the CSV file to read
    - output_file: str, the path to save the filtered CSV file
    """
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # Write the header row to the output file
            headers = next(reader)
            writer.writerow(headers)

            # Filter out rows where the page count is 0
            removed_count = 0
            
            for row in reader:
                page_count = row[3]  # Assuming the page count is in the fourth column (index 3)
                if page_count.isdigit() and int(page_count) > 0:
                    writer.writerow(row)
                else:
                    removed_count += 1

            logging.info(f"Filtered out {removed_count} records with 0 pages from {input_file}.")

    except Exception as e:
        logging.error(f"Error processing CSV file: {e}")


def delete_zero_page_records():
    """
    Deletes all records from the JobSearch table where the last_page_number is 0.
    Logs the number of records deleted.
    """
    with get_session() as session:
        # Query to find all job search records with last_page_number = 0
        zero_page_records = session.query(JobSearch).filter(JobSearch.last_page_number == 0).all()
        
        # Count records to delete
        record_count = len(zero_page_records)
        
        if record_count > 0:
            for record in zero_page_records:
                session.delete(record)

            session.commit()
            logging.info(f"Deleted {record_count} records with last_page_number = 0 from JobSearch table.")
            
        else:
            logging.info("No records found with last_page_number = 0 in JobSearch table.")


input_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/JobSearch.csv')
output_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/CleanedJobSearch.csv')

# Run the function to clean the CSV file
remove_zero_page_records(input_csv_file, output_csv_file)

# Run the cleanup for job search records with last_page_number = 0
delete_zero_page_records()