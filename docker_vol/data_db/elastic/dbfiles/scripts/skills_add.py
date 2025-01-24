from elasticsearch import Elasticsearch
from neo4j import GraphDatabase
import re
import os

# Elasticsearch and Neo4j connection details
ES_HOST = "http://@localhost:9200"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4jpwd"
ELASTIC_INDEX = "jobmarket"
LOG_FILE = "../../../../log/skills.log"

# Function to retrieve skills from Neo4j
def get_skills_from_neo4j():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    skills = set()

    query = '''
    MATCH (n)
    WHERE n:Skill OR n:Skillset
    RETURN n.preferredLabel AS preferredLabel, n.altLabels AS altLabels, n.hiddenLabels AS hiddenLabels
    '''

    with driver.session() as session:
        results = session.run(query)
        for record in results:
            if record["preferredLabel"]:
                skills.add(record["preferredLabel"].lower())
            if record["altLabels"]:
                skills.update(label.lower() for label in record["altLabels"])
            if record["hiddenLabels"]:
                skills.update(label.lower() for label in record["hiddenLabels"])

    driver.close()
    return skills

# Function to normalize text
def normalize_text(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text

# Function to match skills in job description
def match_skills(job_desc, skills_set):
    """
    Matches valid skills from skills_set against job_desc.
    """
    # Normalize the job description for consistent matching
    normalized_desc = normalize_text(job_desc)

    # Match exact skills (full phrases) from skills_set
    matched_skills = set()
    for skill in skills_set:
        # Exact phrase match
        if f" {skill.lower()} " in f" {normalized_desc} ":
            matched_skills.add(skill)
    
    return matched_skills

# Function to log updates
def log_update(job_id, new_skills):
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"job {job_id} updated: {new_skills} added.\n")

# Function to update Elasticsearch
def update_elasticsearch_skills(es, index_name, skills_set):
    query = {
        "_source": ["job_desc", "skills", "job_id"],  # Fetch relevant fields
        "query": {"match_all": {}},
        "size": 100,  # Fetch 100 documents per page
        "sort": [{ "job_id": "asc" }]
    }

    # Initial search with scroll context
    response = es.search(index=index_name, body=query, scroll="1m")
    hits = response.get("hits", {}).get("hits", [])

    while hits:
        for hit in hits:
            job_id = hit["_source"]["job_id"]
            job_desc = hit["_source"].get("job_desc", "")
            existing_skills = set(hit["_source"].get("skills", []))

            # Skip if job_desc is empty
            if not job_desc.strip():
                continue

            # Match skills in job description
            matching_skills = match_skills(job_desc, skills_set)

            # Determine new skills to add
            # Validate matched skills (strictly check against skills_set)
            valid_skills = {
                skill for skill in matching_skills
                if skill in skills_set and (len(skill) > 1 or skill in {"c", "r"})  # Allow valid short skills
            }
            new_skills = valid_skills - existing_skills


            if new_skills:
                updated_skills = existing_skills.union(new_skills)
                print(job_id, updated_skills)

                # Update Elasticsearch
                es.update(index=index_name, id=hit["_id"], body={"doc": {"skills": list(updated_skills)}})

                # Log the update
                #log_update(job_id, new_skills)
                print(f"job {job_id} updated: {new_skills} added.")
        
        # Check for _scroll_id and fetch the next batch
        scroll_id = response.get("_scroll_id")
        if not scroll_id:
            print("No more scroll ID; exiting pagination.")
            break

        # Fetch the next batch of results
        response = es.scroll(scroll_id=scroll_id, scroll="1m")
        hits = response.get("hits", {}).get("hits", [])
        print(f"Fetched {len(hits)} hits in next batch.")  # Debug pagination

# Main execution
if __name__ == "__main__":
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Connect to Elasticsearch and Neo4j
    es = Elasticsearch([ES_HOST])
    skills_set = get_skills_from_neo4j()

    # Update Elasticsearch with matched skills
    update_elasticsearch_skills(es, ELASTIC_INDEX, skills_set)