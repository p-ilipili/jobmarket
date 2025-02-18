# jobmarket
DataScientest - Data Engineering jobmarket project

## 1	Data Extraction
Both scripts, adzuna_extract.py and muse_extract.py, are designed to scrape job offers from two platforms—Adzuna and The Muse. Here's a high-level summary of what they do:

1.1	Scripts Mechanisms
adzuna_extract.py
1.	Scope:
o	Scrapes job offers from Adzuna for specified countries (us, de, fr, ca, gb, ch).
o	Searches within predefined job categories (e.g., engineering, IT, consultancy, teaching).
o	Scrapes up to 50 pages for each combination of country and job category.
2.	Key Operations:
o	Iterates over each country and job category.
o	Uses pagination to access multiple pages of job results.
o	Writes the scraped data into a JSON file named results_adzuna.json.

muse_extract.py
1.	Scope:
o	Designed to scrape job listings from The Muse.
o	Pagination is implemented to scrape multiple pages of job data (up to 500 pages).
2.	Key Operations:
o	No specific filtering as the amount of jobs returned was rather small or empty when using filters.
o	Writes scraped job data into a JSON file named results_muse.json.

LinkedIn and Indeed:
There were attempts to scrape those sites. While they initially succeeded with use of Selenium, there were some issues. It was impossible to scrape large datasets from LinkedIn and Indeed due to several anti-scraping mechanisms. 

## 2	Data Trasformation

