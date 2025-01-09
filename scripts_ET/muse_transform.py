import subprocess
import requests
import json
import pandas as pd
from bs4 import BeautifulSoup as bs
from langdetect import detect
from googletrans import Translator

# Initialize google_trans_lzx translator
translator = Translator()

# Define U.S. states for abbreviation replacement
US_states = {
    "State": [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
        "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
        "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
        "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
        "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
        "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
        "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
    ],
    "Abbreviation": [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS",
        "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
        "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
        "WI", "WY"
    ]
}

states_df = pd.DataFrame(US_states)

# Run shell command in Python
# The source file is defined at the end of this command
result = subprocess.run(
    ["jq",
     """.. | objects | select(.results) | .results[] | {
        job_id : .id,
        job_date : .publication_date,
        category : .categories[].name,
        job_title : .name,
        job_level : .levels[].short_name,
        company : .company.name,
        job_url : .refs.landing_page,
        contract_type : (.contract_type //null),
        location : .locations[].name,
        sal_min : (.salary_min //null),
        sal_max : (.salary_max //null),
        sal : (.salary //null),
        sal_predicted : (.salary_is_predicted //null)}""",
     "results_muse.json"],
    capture_output=True,
    text=True,
)
# Test for checking data structure integrity
# Print the output
# print(result.stdout)

# the obtained data is not an array and has no comma between the elements '}{'}'
# this is adding the required elements
json_data = f"[{result.stdout.replace('}\n{', '},{')}]"

# Test for checking data structure integrity
#print(json_data)
#with open("out.json", "w") as file:
#    file.write(json_data)

# Define a function to format locations
def format_location(location_area):
    formatted_location = []
    remote_flag = 0
    
    for loc in location_area:
        if "Flexible / Remote" in loc:
            remote_flag = 1
            continue

        parts = loc.split(", ")
        if len(parts) == 2:
            city = parts[0].strip()
            country_or_state = parts[1].strip()
            
            # Check if the country_or_state is a U.S. state abbreviation
            state_row = states_df[states_df['Abbreviation'] == country_or_state]
            if not state_row.empty:
                # Replace abbreviation with full state name and add "US" at the start
                state_full = state_row.iloc[0]['State']
                formatted_location = ["US", state_full, city]
            else:
                formatted_location = [country_or_state, city]
        else:
            formatted_location = [loc]  # Keep the format if it doesn’t match expected patterns

    return formatted_location, remote_flag



muse_jobs = json.loads(json_data)

req_header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
}

for job in muse_jobs:
    try:
        #print(job['job_url'])
        response = requests.get(job['job_url'], headers=req_header)
        #response.raise_for_status()  # Check for request errors

        muse_soup = bs(response.content, 'lxml')

        # The text is seperated into multiple html elements -> j_desc_html.
        # Then the text from each element is put into the var j_desc and
        # a line break is added after each element for a cleaner text.
        j_desc_html = muse_soup.find('section', class_ = 'JobIndividualBody_jobBodyContainer__rQGA_')
        j_desc = j_desc_html.get_text(separator="\n", strip=True) if j_desc_html else "Description not found"
        
        job['job_desc'] = str(j_desc)
              
    except requests.RequestException as e:
        job['job_desc'] = f"Error fetching description: {e}"

# Test for checking data structure integrity
#with open("out.json", "w") as file:
#    json.dump(adz_jobs, file, ensure_ascii=False, indent=4)

# specify the fields to translate :
include_fields = ['job_title', 'job_desc']


# Translate specified fields in each job entry
processed_jobs = []  # List to store jobs without errors

# Function to translate text if it's not in English
def translate_text_lzx(text, target_lang='en'):
    if text:
        text = str(text)
        try:
            return translator.translate(text, dest=target_lang).text
        except Exception as e:
            raise ValueError(f"Translation error: {e}")  # Raise an error to skip this job

    raise ValueError("No text provided for translation")  # Raise an error if text is None or empty

# Function to check if text is in English
def is_english(text):
    try:
        return detect(text) == 'en'
    except Exception as e:
        print(f"Error detecting language: {e}")
        return False  # Treat as non-English if detection fails

# Function to remove specified suffixes from text
def remove_suffixes(text, suffixes):
    for suffix in suffixes:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text.strip()

# Suffixes to remove from 'category'
suffixes_to_remove = [' jobs', ' positions', '-stolen']

# Translate specified fields in each job entry
processed_jobs = []  # List to store jobs without errors
en_countries = ['US', 'UK', 'Australia'] # Ads from those countries shouldn't be checked for translation

'''
for job in muse_jobs:
    try:
        # Process each field as needed
        for field in include_fields:
            if field in job:
                # Force conversion to string to handle None values
                original_text = str(job[field])
                # Translate fields
                job[field] = translate_text_lzx(original_text)

        # If processing was successful for all fields, add the job to processed_jobs
        processed_jobs.append(job)

    except ValueError as e:
        # Print the error for debugging and skip this job entry
        print(f"Skipping job {job.get('job_id', 'unknown')} due to error: {e}")
'''

for job in muse_jobs:
    try:
        # Format location and set remote flag
        location_area = job.get('location', [])
        # Ensure location_area is a list, even if it was a string
        if isinstance(location_area, str):
            location_area = [location_area]
        elif location_area is None or not isinstance(location_area, list):
            location_area = []  # Set to an empty list if None or not a list

        formatted_location, remote_flag = format_location(location_area)
        job['location'] = formatted_location
        job['remote'] = remote_flag

        for field in include_fields:
            if field in job:
                original_text = str(job[field])
                location_country = job['location'][0]

                # Skip translation for English-speaking countries
                if location_country in en_countries:
                    job[field] = original_text
                else:
                    # If 'category' field, handle suffixes after translating if needed
                    if field == 'category':
                        if not is_english(original_text):
                            to_correct = translate_text_lzx(original_text)
                        else:
                            to_correct = original_text
                        job[field] = remove_suffixes(to_correct, suffixes_to_remove)
                    else:
                        # Translate non-English fields
                        if not is_english(original_text):
                            job[field] = translate_text_lzx(original_text)
                        else:
                            job[field] = original_text

        # Add the processed job to the final list
        processed_jobs.append(job)

    except Exception as e:
        print(f"Skipping job {job.get('job_id', 'unknown')} due to error: {e}")

# Convert the cleaned list to DataFrame and save to CSV
muse_jobs_df = pd.DataFrame(processed_jobs)

print(muse_jobs_df)
muse_jobs_df.to_csv('../docker_vol/data_ETL/muse_jobs.csv', sep=';', index=False, encoding='utf-8')