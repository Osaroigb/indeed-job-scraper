import os
from scraper_utils.csv_utils import remove_zero_page_records

input_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/JobSearch.csv')
output_csv_file = os.path.join(os.path.dirname(__file__), 'csv_exports/CleanedJobSearch.csv')

# Run the function to clean the CSV file
remove_zero_page_records(input_csv_file, output_csv_file)