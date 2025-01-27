import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from elasticsearch import Elasticsearch

#-------------------    UNDER CONSTRUCTION   -------------------#

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Get data
query = {
    "_source": ["category", "sal_min", "sal_max", "location.country"],
    "query": {
        "range": {
            "sal_min": {
                "gt": 20000
            }
        }
    },
    "size": 10000  # Adjust size as needed to limit the number of returned documents
}

# Execute the query
index_name = "jobmarket"
response = es.search(index=index_name, body=query)

# Extract the data into a list of dictionaries
hits = response['hits']['hits']
data = []
for hit in hits:
    source = hit['_source']
    # Flatten location.country into country
    flat_entry = {
        "category": source.get("category"),
        "country": source.get("location", {}).get("country"),
        "sal_min": source.get("sal_min"),
        "sal_max": source.get("sal_max"),
    }
    data.append(flat_entry)

# Convert to a Pandas DataFrame
df = pd.DataFrame(data)


print(df.head())
#df.info()

# use sal_min info for empty sal_max fields
df['sal_max'] = df['sal_max'].fillna(df['sal_min'])
#df.info()

# create salary column to have a unique value.
# Salary = average of sal_min & sal_max
df['salary'] = df[['sal_min', 'sal_max']].mean(axis=1)
#df.info()

# remove min and max columns
df = df.drop(columns=['sal_min', 'sal_max'])
df.info()

#no outliers giving the describe result
#print(df['salary'].describe())

# define explanatory and target vars
feats = df.drop('salary',axis=1)
target = df['salary']

#feats.info()

# Split into train and test set
X_train, X_test, y_train, y_test = train_test_split(feats, target, test_size=0.20, random_state = 42)

# One hot encoding for explanatory vars category and country
# The drop = 'first' parameter allows to delete one of the columns created by the OneHotEncoder
# and thus avoid a multicolinearity problem

onehot = OneHotEncoder(drop = 'first', sparse_output = False)

cat = ['category', 'country']

X_train[cat] = onehot.fit_transform(X_train[cat])
X_test[cat] = onehot.transform(X_test[cat])

# No standardization as there's no numerical column except salary
'''
regressor = LinearRegression()
regressor.fit(X_train, y_train)

coeffs = list(regressor.coef_)
coeffs.insert(0, regressor.intercept_)

feats2 = list(feats.columns)
feats2.insert(0, 'Intercept')

coefficients = pd.DataFrame({'Estimated value': coeffs}, index=feats2)

display(coefficients)
'''