import os
import csv
from config import logging
from database import get_session
from database.models import JobSearch, JobListing


def db_table_to_csv(query, filename):
    """
    Exports a database table query result to a CSV file.
    """
    try:
        # Fetch all records
        records = query.all()

        if not records:
            logging.warning(f"No data found for {filename}.")
            return

        # Create CSV directory if it doesn't exist
        csv_dir = 'csv_exports'
        os.makedirs(csv_dir, exist_ok=True)

        # Define the CSV file path
        csv_file_path = os.path.join(csv_dir, f"{filename}.csv")

        # Write to CSV file
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(records[0].__table__.columns.keys())  # Write header

            for record in records:
                writer.writerow([getattr(record, col) for col in record.__table__.columns.keys()])

        logging.info(f"{filename}.csv has been created with {len(records)} records.")

    except Exception as e:
        logging.error(f"Failed to export {filename} to CSV: {e}")


def export_tables_to_csv():
    """
    Exports JobSearch and JobListing tables to separate CSV files.
    """
    with get_session() as session:
        db_table_to_csv(session.query(JobSearch), 'JobSearch')
        # db_table_to_csv(session.query(JobListing), 'JobListing') # TODO: comment for testing

    logging.info("All tables have been exported to CSV.")