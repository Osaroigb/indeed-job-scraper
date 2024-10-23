import os
import re

#? Define the input and output file names using absolute paths
input_file = os.path.join(os.path.dirname(__file__), 'target_jobs.txt')
output_file = os.path.join(os.path.dirname(__file__), 'cleaned_jobs.txt')

#* Open the input file for reading and the output file for writing
with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        #! Use regex to remove text within parentheses
        cleaned_line = re.sub(r'\s*\(.*?\)\s*', ' ', line).strip()
        
        #? Write the cleaned line to the output file
        outfile.write(cleaned_line + '\n')

print(f"Cleaned job titles have been written to '{output_file}'.")