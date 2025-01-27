import csv
import json
from elasticsearch import Elasticsearch

# Elasticsearch connection setup
es = Elasticsearch("http://@jm-elastic:9200")

# Define the index name
index_name = "jobmarket"

# CSV file processing
csv_files = ["/opt/airflow/scripts_ETL/adz_jobs.csv"]
#csv_files = ["adz_jobs.csv", "muse_jobs.csv"]

def process_location(location):
    """Splits the location into country and region/city."""
    location_parts = eval(location)  # Convert string representation of list to list
    country = location_parts[0]
    region_city = location_parts[1:] if len(location_parts) > 1 else []
    return country, region_city

def process_remote(remote):
    """Maps numeric remote values to text."""
    mapping = {0: "onsite", 1: "hybrid", 2: "remote"}
    if remote.isdigit():
        numeric_value = int(remote)
        return numeric_value, mapping.get(numeric_value, "")
    return None, None

for file in csv_files:
    with open(file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            job_id = row.get("job_id")
            if not job_id:
                continue  # Skip rows without job_id

            # Check if the document with the same job_id already exists
            if es.exists(index=index_name, id=job_id):
                print(f"Document with job_id {job_id} already exists. Skipping.")
                continue

            location = row.get("location", "[]")
            country, region_city = process_location(location)

            remote_numeric, remote_text = process_remote(row.get("remote", ""))

            document = {
                "job_id": int(job_id),
                "job_date": row.get("job_date"),
                "category": row.get("category"),
                "job_title": row.get("job_title"),
                "job_level": row.get("job_level"),
                "company": row.get("company"),
                "job_url": row.get("job_url"),
                "contract_type": row.get("contract_type"),
                "location": {
                    "country": country,
                    "region_city": region_city
                },
                "sal_min": float(row.get("sal_min", 0)) if row.get("sal_min") else None,
                "sal_max": float(row.get("sal_max", 0)) if row.get("sal_max") else None,
                "sal": float(row.get("sal", 0)) if row.get("sal") else None,
                "sal_predicted": row.get("sal_predicted", "false").lower() == "true",
                "job_desc": row.get("job_desc"),
                "remote": {
                    "r_numeric": remote_numeric,
                    "r_text": remote_text
                },
                "skills": []
            }

            # Index the document into Elasticsearch
            es.index(index=index_name, id=job_id, document=document)
            print(f"Document with job_id {job_id} indexed successfully.")

print("All documents have been indexed.")
