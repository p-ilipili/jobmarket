import os
import shutil
from datetime import datetime
import json
import jq
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
from langdetect import detect
from googletrans import Translator

# File and folder setup
file_name = "muse_jobs.csv"
backup_folder = "./old"
os.makedirs(backup_folder, exist_ok=True)

# Backup existing CSV file
if os.path.exists(file_name):
    creation_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    backup_file = f"muse_jobs_{creation_date}.csv"
    backup_path = os.path.join(backup_folder, backup_file)
    shutil.move(file_name, backup_path)
    print(f"Moved {file_name} to {backup_path}")

# Initialize translator
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

# Process JSON data
all_results = []
with open('results_muse.json', 'r') as f:
    for line in f:
        page_data = json.loads(line)
        if 'results' in page_data:
            all_results.extend(page_data['results'])

filter_expression = """.. | objects | select(.results) | .results[] | {
    job_id: .id,
    job_date: .publication_date,
    category: .categories[].name,
    job_title: .name,
    job_level: .levels[].short_name,
    company: .company.name,
    job_url: .refs.landing_page,
    contract_type: (.contract_type // null),
    location: .locations[].name,
    sal_min: (.salary_min // null),
    sal_max: (.salary_max // null),
    sal: (.salary // null),
    sal_predicted: (.salary_is_predicted // null)
}"""
result = jq.compile(filter_expression).input(all_results).all()
print(result)

# Convert results to JSON
json_data = json.dumps(result, indent=4)
print(json_data)
# Function to format locations
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

            state_row = states_df[states_df['Abbreviation'] == country_or_state]
            if not state_row.empty:
                state_full = state_row.iloc[0]['State']
                formatted_location = ["US", state_full, city]
            else:
                formatted_location = [country_or_state, city]
        else:
            formatted_location = [loc]

    return formatted_location, remote_flag

# Load transformed JSON data
muse_jobs = json.loads(json_data)
#print(f"Number of jobs extracted after jq filtering: {len(result)}")
#print(f"Number of jobs in JSON data: {len(muse_jobs)}")
#print(muse_jobs)

# Headers for HTTP requests
req_header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
}

# Fetch job descriptions and process fields
processed_jobs = []
for job in muse_jobs:
    try:
        response = requests.get(job['job_url'], headers=req_header)
        muse_soup = bs(response.content, 'lxml')
        j_desc_html = muse_soup.find('section', class_='JobIndividualBody_jobBodyContainer__rQGA_')
        job['job_desc'] = j_desc_html.get_text(separator="\n", strip=True) if j_desc_html else "Description not found"

        location_area = job.get('location', [])
        if isinstance(location_area, str):
            location_area = [location_area]
        formatted_location, remote_flag = format_location(location_area)
        job['location'] = formatted_location
        job['remote'] = remote_flag

        for field in ['job_title', 'job_desc']:
            original_text = str(job[field])
            if detect(original_text) != 'en':
                job[field] = translator.translate(original_text, dest='en').text

        processed_jobs.append(job)

    except Exception as e:
        print(f"Skipping job {job.get('job_id', 'unknown')} due to error: {e}")

# Save to CSV
muse_jobs_df = pd.DataFrame(processed_jobs)
muse_jobs_df.to_csv(file_name, sep=';', index=False, encoding='utf-8')
