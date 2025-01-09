from typing import Union, Optional, List
from fastapi import FastAPI, HTTPException, Depends, Header, status, Query

app = FastAPI(
    title = "Jobmarket Data - A collection of job offers",
    description = "Query interesting data bout job offers. Be it about money, skills, locations, ..."
)

# API Healthcheck
@api.get('/hc', name="API Healthcheck")
def get_hc():
    """Check the status of the API
    """
    return {"The API is running fine"}

@app.get("/")
def read_root():
    return {"Hello": "World"}