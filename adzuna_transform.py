import subprocess
import requests
import json
import pandas as pd
from bs4 import BeautifulSoup as bs
from langdetect import detect
from googletrans import Translator

# Initialize google_trans_lzx translator
translator = Translator()

# Run shell command in Python to use jq
# The source file is defined at the end of this command
result = subprocess.run(
    ["jq",
     """.. | objects | select(.results) | .results[] | {
        job_id : .id,
        job_date : .created,
        category : (.category.label | gsub(" Jobs$"; "")),
        job_title : .title,
        job_level : (.level //null),
        company : .company.display_name,
        job_url : .redirect_url,
        contract_type : .contract_type,
        location : (if .location.area then .location.area 
                | gsub("Deutschland"; "Germany")
                | gsub("Schweiz"; "Switzerland")
                | gsub("Kanton "; "")
                else .location.area end),
        sal_min : .salary_min,
        sal_max : .salary_max,
        sal : (.salary //null),
        sal_predicted : .salary_is_predicted}""",
     "results_adzuna.json"],
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

adz_jobs = json.loads(json_data)

for job in adz_jobs:
    try:
        #print(job['job_url'])
        response = requests.get(job['job_url'])
        #response.raise_for_status()  # Check for request errors

        adz_soup = bs(response.content, 'lxml')

        # The text is seperated into multiple html elements -> j_desc_html.
        # Then the text from each element is put into the var j_desc and
        # a line break is added after each element for a cleaner text.
        j_desc_html = adz_soup.find('section', class_ = 'adp-body')
        j_desc = j_desc_html.get_text(separator="\n", strip=True) if j_desc_html else "Description not found"
        
        job['job_desc'] = j_desc
              
    except requests.RequestException as e:
        job['job_desc'] = f"Error fetching description: {e}"

# Test for checking data structure integrity
#with open("out.json", "w") as file:
#    json.dump(adz_jobs, file, ensure_ascii=False, indent=4)

# specify the fields to translate :
include_fields = ['category','job_title', 'job_desc']

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

for job in adz_jobs:
    try:
        job['remote'] = 0
        for field in include_fields:
            if field in job:
                original_text = str(job[field])

                # Check if location is in en_countries before translating
                location_country = job.get('location', [])[0]  # Get the country from location
                if location_country in en_countries:
                    # Skip translation for English-speaking countries
                    job[field] = original_text
                else:
                    # Check if 'category' field, handle suffixes after translating if needed
                    if field == 'category':
                        if not is_english(original_text):
                            to_correct = translate_text_lzx(original_text)
                        else:
                            to_correct = original_text
                        job[field] = remove_suffixes(to_correct, suffixes_to_remove)

                    # Other fields, translate only if not in English
                    else:
                        if not is_english(original_text):
                            job[field] = translate_text_lzx(original_text)
                        else:
                            job[field] = original_text

        # Add the processed job to the final list if successful
        processed_jobs.append(job)

    except Exception as e:
        print(f"Skipping job {job.get('job_id', 'unknown')} due to error: {e}")

# Convert the cleaned list to DataFrame and save to CSV
adz_jobs_df = pd.DataFrame(processed_jobs)

print(adz_jobs_df)
adz_jobs_df.to_csv('adz_jobs.csv', sep=';', index=False, encoding='utf-8')