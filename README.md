# jobmarket
DataScientest - Data Engineering jobmarket project

Data extraction and transformation are tasks done simultaneously (adzuna and muse) and consecutively in Airflow.

## 1	Data Extraction
Both scripts, adzuna_extract.py and muse_extract.py, are designed to scrape job offers from two platforms—Adzuna and The Muse. Here's a high-level summary of what they do:

## 1.1	Scripts Mechanisms
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

The transformation process is responsible for cleaning, standardizing, and enriching the raw job offer data extracted from Adzuna and The Muse. This step ensures that the data is structured and usable for downstream analysis.

## 2.1 Initial Processing

This step involves extracting relevant job attributes from raw JSON data, handling backups, and preparing the dataset for deeper transformations.

<ins>Backup Management:</ins><br>
If an existing transformed file is found (adz_jobs.csv or muse_jobs.csv), it is archived in the old/ folder, preserving historical data.

<ins>Data Extraction & Parsing:</ins><br>
Uses jq (for Adzuna) to extract relevant job attributes (title, company, location, description, salary, etc.).
Loads raw JSON data (for The Muse) into a Pandas DataFrame, converting it into a structured tabular format.

## 2.2 Standardization and Enrichment

After extraction, the data undergoes multiple cleaning and enrichment steps:

<ins>Translation & Language Detection:</ins> <br>
Detects the language of job descriptions using langdetect.
Uses googletrans to translate non-English descriptions into English for uniformity.

<ins>Location Standardization:</ins><br>
Extracts and structures city, state, and country fields.
Replaces U.S. state abbreviations with full names.
Identifies remote jobs based on specific keywords and flags them.

<ins>Data Cleaning:</ins><br>
Removes incomplete or irrelevant job postings.
Handles missing values and ensures consistent formatting.
Output Storage: Saves the cleaned, structured job dataset as a Pandas DataFrame, which is then exported as adz_jobs.csv and muse_jobs.csv.

## 3 Data Importation
The third stage of the data pipeline focuses on integrating transformed job data and skillset information into two databases:

Neo4j: Used for managing skill relationships and ontology-based queries.
Elasticsearch: Used for indexing and efficiently searching job offers.
Note: Only the task of loading the job CSV files into Elasticsearch is managed within an Airflow pipeline.

## 3.1 Loading the ESCO Skillset into Neo4j
The ESCO (European Skills, Competences, Qualifications, and Occupations) dataset is a classification system developed by the European Commission. It provides a structured taxonomy of:

Skills & Competences: The knowledge, abilities, and expertise required for different jobs.
Occupations: Job titles and roles linked to relevant skills.
Qualifications: Recognized certifications and education levels.

## 3.1.1 ESCO Data Import and Graph Structure
The Neo4j import script (import_ESCO_csv_en.cql) is responsible for loading the ESCO dataset into a graph database, creating relationships between occupations, skills, and hierarchical categories.

<ins>Key Steps:</ins>
1. Index Creation for Faster Queries
Creates indexes on skills and occupations using fields like preferredLabel, altLabels, ISCOGroup, and conceptUri.
2. Loading Nodes
Skills: Imported from skills_en.csv and stored as (:Skill) nodes.
Skill Groups: Imported from skillGroups_en.csv and stored as (:Skill:Skillgroup) nodes.
Occupations: Imported from occupations_en.csv and stored as (:Occupation) nodes.
ISCO Classification: ISCOGroup nodes are created to categorize occupations.
3. Establishing Relationships
(:Occupation)-[:REQUIRES]->(:Skill): Connects jobs to the necessary skills.
(:Skill)-[:BROADER_THAN]->(:Skill): Defines hierarchical relationships between skills.
(:Occupation)-[:HAS_ISCO_GROUP]->(:ISCOGroup): Maps occupations to their ISCO classification.
(:Skill)-[:RELATED_TO]->(:Skill): Links similar or interchangeable skills.
This structured graph enables efficient job-skill matching and recommendation queries within Neo4j.

## 3.2 Importing Job Data into Elasticsearch
Elasticsearch is used to store and index job postings, making them easily searchable based on job title, location, company, and skills.

## 3.2.1 Creating the Elasticsearch Database Schema
The Elasticsearch index mapping is defined in mapping_create.json. This file structures the job data and configures analyzers for efficient search.

Key Schema Features
Tokenization for Search Optimization:

Uses an edge n-gram tokenizer to allow partial matches on job titles and descriptions.
Normalizes text using lowercase and ASCII folding to improve search results.
Job Data Fields:

job_id: Unique identifier for each job.
job_title: Indexed as both text (for full-text search) and keyword (for exact matches).
category: Job classification, indexed similarly.
location: Stored as structured data (country, region_city).
skills: Stored as keywords to facilitate filtering by required skills.
sal_min, sal_max: Salary range stored as floating-point numbers.
remote: A structured field with numerical and text-based values for job flexibility.
This mapping ensures fast and efficient job searches with autocomplete and filtering capabilities.

## 3.2.2 Loading Job Data into Elasticsearch
The script elastic_import.py handles the actual import of job postings from the previously transformed CSV files (adz_jobs.csv and muse_jobs.csv) into Elasticsearch.

<ins>Key Steps</ins>
1. Connecting to Elasticsearch
Uses the Python Elasticsearch client to communicate with the cluster at jm-elastic:9200.
2. Processing CSV Files
Reads job postings from adz_jobs.csv (and optionally muse_jobs.csv).
Splits location into structured country and region/city fields.
Maps remote values (0, 1, 2) to text labels (onsite, hybrid, remote).
3. Indexing Jobs into Elasticsearch
Each job posting is converted into a structured JSON document.
The script bulk-inserts job data into the jobmarket index.
This ensures that job postings are searchable in real-time, with support for full-text search, filtering, and autocomplete.
