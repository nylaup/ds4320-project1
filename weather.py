import requests
import pandas as pd

#coordinates for boroughs of NYC to query 
BOROUGH_COORDS = {
    "Manhattan":     (40.7831, -73.9712),
    "Brooklyn":      (40.6782, -73.9442),
    "Queens":        (40.7282, -73.7949),
    "Bronx":         (40.8448, -73.8648),
    "Staten Island": (40.5795, -74.1502),
}

#empty dataframe
weather_dfs = []

#query hourly for each borough to get temp and code 
for borough, (lat, lon) in BOROUGH_COORDS.items():
    r = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": "2025-01-01",
            "end_date": "2025-03-31",
            "hourly": "temperature_2m,weathercode",
            "timezone": "America/New_York",
            "temperature_unit": "fahrenheit"
        }
    )
    data = r.json()
    df = pd.DataFrame({ #compile queried weather info into dataframe 
        "datetime": pd.to_datetime(data["hourly"]["time"]),
        "temperature": data["hourly"]["temperature_2m"],
        "weathercode": data["hourly"]["weathercode"],
        "borough": borough
    })
    weather_dfs.append(df)

weather_df = pd.concat(weather_dfs)
weather_df["weather_id"] = range(1, len(weather_df) + 1) 

weather_df.to_csv('Weather.csv')