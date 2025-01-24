from fastapi import FastAPI, HTTPException, Query, Depends
from contextlib import asynccontextmanager
from neo4j import GraphDatabase
from elasticsearch import Elasticsearch
from pydantic import BaseModel
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import BytesIO
from fastapi.responses import StreamingResponse, HTMLResponse
import matplotlib
matplotlib.use("Agg")

# Neo4j and Elasticsearch configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4jpwd"
ELASTICSEARCH_HOST = "http://localhost:9200"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
es = Elasticsearch(ELASTICSEARCH_HOST)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield {"driver": driver, "es": es}
    driver.close()
    es.transport.close()

app = FastAPI(
    title="Jobmarket Data - A collection of job offers",
    description="Query interesting data about job offers. Be it about money, skills, locations, ...",
    lifespan=lifespan
)

class SkillOccupationResponse(BaseModel):
    skill: str
    occupation: str

# API Healthcheck
@app.get('/status', name="API Healthcheck")
def get_hc():
    """Check the status of the API"""
    return {"message": "The API is running fine"}

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Neo4j - Skills Endpoint
@app.get("/skills", response_model=list[SkillOccupationResponse])
def get_skills(skill_name: str = Query(..., description="Name of the skill to search for")):
    query = (
        "MATCH (n:Occupation)-[rel]-(c:Skill) "
        "WHERE toLower(c.preferredLabel) CONTAINS toLower($skill_name) "
        "RETURN c.preferredLabel AS skill, n.preferredLabel AS occupation"
    )

    try:
        with driver.session() as session:
            results = session.run(query, skill_name=skill_name)
            
            response = [
                SkillOccupationResponse(skill=record["skill"], occupation=record["occupation"])
                for record in results
            ]

        if not response:
            raise HTTPException(status_code=404, detail="No corresponding skill found")

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying the database: {str(e)}")


# Elasticsearch Endpoint
@app.get("/min-max-salary")
def min_max_salary(min_max: str = Query(..., description="Enter 'min' or 'max' for the highest or lowest salary per job category")):
    min_max = min_max.lower()

    if min_max not in ["min", "max"]:
        raise HTTPException(status_code=400, detail="Invalid input. Please enter 'min' or 'max'.")

    query = {
        "size": 0,
        "query": {
            "range": {
                f"sal_{min_max}": {
                    "gt": 20000
                }
            }
        },
        "aggs": {
            "unique_categories": {
                "terms": {
                    "field": "category.keyword"
                },
                "aggs": {
                    f"{min_max}_sal_{min_max}": {
                        min_max: {
                            "field": f"sal_{min_max}"
                        }
                    }
                }
            }
        }
    }

    try:
        response = es.search(index="jobmarket", body=query)
        categories = response["aggregations"]["unique_categories"]["buckets"]

        # Use pandas DataFrame to format the response
        data = {
            "Category": [category['key'] for category in categories],
            "Entries": [category['doc_count'] for category in categories],
            f"{min_max}_salary": [category[f"{min_max}_sal_{min_max}"]["value"] for category in categories]
        }
        df = pd.DataFrame(data)

        return df.to_dict(orient="records")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Elasticsearch: {str(e)}")

# Elasticsearch Endpoint for salary variance
@app.get("/sal-variance")
def sal_variance():
    query1 = {
        "size": 0,
        "query": {
            "range": {
                "sal_min": {
                    "gt": 20000
                }
            }
        },
        "aggs": {
            "unique_categories": {
                "terms": {
                    "field": "category.keyword"
                },
                "aggs": {
                    "lowest_sal_min": {
                        "min": {
                            "field": "sal_min"
                        }
                    },
                    "highest_sal_max": {
                        "max": {
                            "field": "sal_max"
                        }
                    }
                }
            }
        }
    }

    query2 = {
        "size": 0,
        "query": {
            "range": {
                "sal_min": {
                    "gt": 20000
                }
            }
        },
        "aggs": {
            "countries": {
                "terms": {
                    "field": "location.country"
                },
                "aggs": {
                    "unique_categories": {
                        "terms": {
                            "field": "category.keyword"
                        },
                        "aggs": {
                            "lowest_sal_min": {
                                "min": {
                                    "field": "sal_min"
                                }
                            },
                            "highest_sal_max": {
                                "max": {
                                    "field": "sal_max"
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    try:
        # First query for category-wise data
        response1 = es.search(index="jobmarket", body=query1)
        categories = response1["aggregations"]["unique_categories"]["buckets"]

        data1 = {
            "Category": [category['key'] for category in categories],
            "sal_min": [category['lowest_sal_min']['value'] for category in categories],
            "sal_max": [category['highest_sal_max']['value'] for category in categories]
        }
        df1 = pd.DataFrame(data1)

        # Second query for country-wise data
        response2 = es.search(index="jobmarket", body=query2)
        countries_data = response2["aggregations"]["countries"]["buckets"]

        rows = []
        for country in countries_data:
            country_name = country["key"]
            for category in country["unique_categories"]["buckets"]:
                rows.append({
                    "Country": country_name,
                    "Category": category["key"],
                    "sal_min": category["lowest_sal_min"]["value"],
                    "sal_max": category["highest_sal_max"]["value"]
                })

        df2 = pd.DataFrame(rows)
        #print(df2)

        # Create the first matplotlib bar chart (category-wise)
        plt.figure(figsize=(12, 8))
        plt.subplot(2, 1, 1)
        colors = plt.cm.Pastel1.colors

        for i, category in enumerate(df1.Category):
            plt.bar(i, df1.sal_min[i], alpha=0.8, color=colors[1 % len(colors)])
            plt.bar(i, df1.sal_max[i], bottom=df1.sal_min[i], alpha=0.8, color=colors[2 % len(colors)])

        plt.xticks(range(len(df1)), df1.Category, rotation=45, ha="right")
        plt.xlabel("Category")
        plt.ylabel("Salary")
        plt.title("Salary Variance by Category")

        # Create the second matplotlib bar chart (country-wise)
        categories = df2["Category"].unique()
        countries = df2["Country"].unique()
        bar_width = 0.1
        x_positions = np.arange(len(countries))

        plt.subplot(2, 1, 2)
        tab20_colors = plt.cm.tab20.colors
        for i, category in enumerate(categories):
            # Filter and align data for the current category
            category_data = df2[df2["Category"] == category].set_index("Country").reindex(countries).fillna(0)

            # ---------     NOTE     --------#
            #some categories are empty so there are spaces in the graphic of query2

            # Debug category data
            #print(f"Debug for category: {category}")
            #print(category_data)

            # Ensure country order is consistent
            #category_data = category_data.set_index("Country").reindex(countries).fillna(0)

            positions = x_positions + (i - len(categories) / 2) * bar_width
            plt.bar(positions, category_data["sal_min"], width=bar_width, alpha=0.7, color=tab20_colors[2 * i % len(tab20_colors)])
            plt.bar(positions, category_data["sal_max"], width=bar_width, bottom=category_data["sal_min"], alpha=0.7, color=tab20_colors[(2 * i + 1) % len(tab20_colors)], label=category)

        plt.xticks(x_positions, countries, rotation=45, ha="right")
        plt.xlabel("Country")
        plt.ylabel("Salary")
        plt.title("Salary Variance by Country and Category")
        plt.legend()

        # Save the plots to a BytesIO buffer
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Elasticsearch: {str(e)}")
