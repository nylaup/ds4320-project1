import requests
import pandas as pd
import time
import logging

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='weather.log'
)
logger = logging.getLogger(__name__)

#coordinates for boroughs of NYC to query 
BOROUGH_COORDS = {
    "Manhattan":     (40.7831, -73.9712),
    "Brooklyn":      (40.6782, -73.9442),
    "Queens":        (40.7282, -73.7949),
    "Bronx":         (40.8448, -73.8648),
    "Staten Island": (40.5795, -74.1502),
}

#set timeframe 
START_DATE = "2016-01-01"
END_DATE   = "2019-12-31"

#empty dataframe
weather_dfs = []

#query hourly for each borough to get temp and code 
for borough, (lat, lon) in BOROUGH_COORDS.items():
    try: 
        logger.info(f"Fetching weather for {borough}...")
        r = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": START_DATE,
                "end_date": END_DATE, 
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
        df["datetime"] = df["datetime"].dt.tz_localize(None)
        logger.info(f"{borough}: {df.shape[0]:,} rows fetched") 
        weather_dfs.append(df)
        time.sleep(1)

    except Exception as e:
        logger.error(f"Failed to fetch weather for {borough}: {e}")
        print(f"Failed to fetch weather for {borough}: {e}")
        continue  # skip failed borough, don't crash entire script

weather_df = pd.concat(weather_dfs, ignore_index=True)
weather_df.index.name = "weather_id" 

weather_df.to_parquet('data/Weather.parquet')
