import subprocess
import requests
import json
import pandas as pd
from bs4 import BeautifulSoup as bs

# Run shell command in Python
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

# Print the output
print(result.stdout)

# the obtained data is not an array and has no comma between the elements '}{'}'
# this is adding the required elements
json_data = f"[{result.stdout.replace('}\n{', '},{')}]"

#print(json_data)

#with open("out.json", "w") as file:
#    file.write(json_data)

muse_jobs = json.loads(json_data)

req_header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
}

for job in muse_jobs:
    try:
        print(job['job_url'])
        response = requests.get(job['job_url'], headers=req_header)
        response.raise_for_status()  # Check for request errors

        muse_soup = bs(response.content, 'lxml')

        # The text is seperated into multiple html elements -> j_desc_html.
        # Then the text from each element is put into the var j_desc and
        # a line break is added after each element for a cleaner text.
        j_desc_html = muse_soup.find('section', class_ = 'JobIndividualBody_jobBodyContainer__rQGA_')
        j_desc = j_desc_html.get_text(separator="\n", strip=True) if j_desc_html else "Description not found"
        
        job['job_desc'] = j_desc
              
    except requests.RequestException as e:
        job['job_desc'] = f"Error fetching description: {e}"


muse_jobs_df = pd.DataFrame(muse_jobs)

print(muse_jobs_df)
muse_jobs_df.to_csv('muse_jobs.csv', sep=';', index=False, encoding='utf-8')