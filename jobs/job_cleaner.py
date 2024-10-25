import re
from config import logging


def clean_job_titles(input_file, output_file):

    #* Open the input file for reading and the output file for writing
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            #! Use regex to remove text within parentheses
            cleaned_line = re.sub(r'\s*\(.*?\)\s*', ' ', line).strip()
            
            #? Write the cleaned line to the output file
            outfile.write(cleaned_line + '\n')

    logging.info(f"Cleaned job titles have been written to '{output_file}'.")