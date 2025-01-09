from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import csv
import re
import random
from datetime import datetime, timedelta, timezone
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
# Get the current date in UTC
current_date = datetime.now(timezone.utc)
# Initialize the translator
translator = GoogleTranslator()
# Define download path
download_path = "job_listings2.csv"
# Set up the WebDriver
driver = webdriver.Chrome()
# List of URLs to scrape
urls = [
    'https://de.indeed.com/jobs?q=Data+Analyst&l=Deutschland&from=searchOnDesktopSerp'
]
# Initialize an empty set to store unique IDs and avoid duplicates
unique_ids = set()
# Function to generate a unique 8-digit ID
def generate_unique_id():
    while True:
        new_id = random.randint(10000000, 99999999)
        if new_id not in unique_ids:
            unique_ids.add(new_id)
            return new_id
# Initialize list to store job listings
job_listings = []
def translate_text(text, src_lang='de', dest_lang='en'):
    """Helper function to handle translation with error handling."""
    try:
        return translator(source=src_lang, target=dest_lang).translate(text)
    except Exception as e:
        print(f"Translation error for text '{text}': {e}")
        return text  # Return original text if translation fails
def scrape_page():
    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Loop through each job card and extract information
    for job_card in soup.find_all('div', class_='job_seen_beacon'):
        job = {}
        #with open("job_card.txt", "w") as file1:
        #    print(job_card, file=file1)
        # Generate and assign a unique 8-digit ID to each job
        job['job_id'] = generate_unique_id()
        # Extract job title and translate to English
        title = job_card.find('h2', class_='jobTitle')
        #print(title.text)
        if title:
            translated_title = translate_text(title.text.strip())
            job['title'] = translated_title
            
            # Determine level based on keywords in the translated title
            if "Junior" in translated_title or "junior" in translated_title:
                job['Level'] = "Junior"
            elif "Senior" in translated_title or "senior" in translated_title:
                job['Level'] = "Senior"
            else:
                job['Level'] = "Mid"
        else:
            job['title'] = None
            job['Level'] = None
        # Extract company name
        company = job_card.find('span', class_='css-1h7lukg eu4oa1w0')
        job['company'] = company.text.strip() if company else None
        # Extract the job summary from jobDescriptionText div
        # Extract job summary or snippet and translate to English
        summary_temp = job_card.find('div', class_='jobsearch-JobComponent-description css-16y4thd eu4oa1w0')
        #summary_temp = job_card.find('div', attrs={'id': 'jobDescriptionText','class': 'jobsearch-JobComponent-description css-16y4thd eu4oa1w0'})
        # Extract text from all <p> and <li> tags
        with open("soupss.txt", "w") as file1:
            print(summary_temp, file=file1)
        p_texts = [p.get_text() for p in summary_temp.find_all('p')]
        li_texts = [li.get_text() for li in summary_temp.find_all('li')]

        # Combine all extracted text
        all_text = p_texts + li_texts
        
        summary = all_text.get_text(separator="\n", strip=True) if summary_temp else "Description not found"
        print(summary)
        #job['summary'] = translate_text(summary.text.strip()) if summary else None
        job['summary'] = translate_text(summary.text.strip()) if summary else None
        # Extract Salary and translate to English
        salary = job_card.find('div', class_='metadata salary-snippet-container css-1f4kgma eu4oa1w0')
        job['salary'] = translate_text(salary.text.strip()) if salary else None
        # Extract Job type, clean it, and translate to English
        contract_type = job_card.find('li', class_='metadata css-1f4kgma eu4oa1w0')
        if contract_type:
            cleaned_contract_type = re.sub(r'\s+\+\d', '', contract_type.text.strip())
            job['contract_type'] = translate_text(cleaned_contract_type)
        else:
            job['contract_type'] = translate_text("Vollzeit")
        # Extract job location and other details
        location = job_card.find('div', class_='css-1restlb eu4oa1w0')
        job['location'] = location.text.strip() if location else None
        job_date = job_card.find('span', class_='css-1yxm164 eu4oa1w0')
        if job_date:
            job_date_text = re.sub(r"(vor\s+|Tagen)", "", job_date.text.strip())
            try:
                days_ago = int(job_date_text)
                job['job_date'] = (current_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            except ValueError:
                job['job_date'] = current_date.strftime("%Y-%m-%d")
        else:
            job['job_date'] = None
        # Add job data to list
        job_listings.append(job)
# Loop over each URL and scrape
for url in urls:
    driver.get(url)
    time.sleep(5)
    page_limit = 1
    page_count = 0
    while page_count < page_limit:
        scrape_page()
        page_count += 1
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            next_button = soup.find('a', {'aria-label': 'Next Page', 'class': 'css-akkh0a e8ju0x50'})
            if next_button and 'href' in next_button.attrs:
                next_url = 'https://de.indeed.com' + next_button['href']
                driver.get(next_url)
                time.sleep(5)
            else:
                print("No more pages to scrape for this URL.")
                break
        except NoSuchElementException:
            print("No more pages to scrape for this URL.")
            break

# Convert the cleaned list to DataFrame and save to CSV
indeed_jobs_df = pd.DataFrame(job_listings)

#print(adz_jobs_df)
indeed_jobs_df.to_csv('indeed_jobs.csv', sep=';', index=False, encoding='utf-8')
'''
# Save data to CSV in a single column
with open(download_path, mode='w', newline='', encoding='utf-8') as file:
    # Specify the column headers for the CSV
    fieldnames = ["job_id", "title", "Level", "company", "summary", "salary", "contract_type", "location", "Remote/Hybride", "job_date"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    # Write the header row
    writer.writeheader()
    # Write each job listing as a row in the CSV
    for job in job_listings:
        writer.writerow(job)
print(f"Data saved successfully at {download_path}")
# Close the browser
driver.quit()
'''