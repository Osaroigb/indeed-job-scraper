import csv
import logging
from config import logging


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