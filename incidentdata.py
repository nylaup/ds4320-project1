import pandas as pd
import requests

url = "https://data.cityofnewyork.us/api/v3/views/76xm-jjuj/query.json" 
API_KEY = KEY

params = {
    "$query": """SELECT * 
    WHERE incident_datetime >= '2025-01-01'
    AND incident_datetime < '2026-01-01'
    LIMIT 1000 """
}

headers = {
    "X-App-Token": API_KEY
}

r = requests.get(url, headers=headers, params=params)
data = r.json()

df = pd.DataFrame(data["rows"], columns=[col["name"] for col in data["meta"]["view"]["columns"]])

df.to_csv('Incidents.csv')