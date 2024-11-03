import requests
import json
import pandas as pd
from bs4 import BeautifulSoup as bs

url="https://www.themuse.com/jobs/siemens/elektrofachkrafte-wmd-im-schaltschrankbau"
res = requests.get(url)
test_soup = bs(res.content,'lxml')

j_desc_html = test_soup.find('section', class_ = 'JobIndividualBody_jobBodyContainer__rQGA_')
j_desc = j_desc_html.get_text(separator="\n", strip=True) if j_desc_html else "Description not found"
print(j_desc)