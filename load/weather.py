import requests
import pandas as pd
import time
import logging

#create logger 
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='weather.log'
)
logger = logging.getLogger(__name__)

#coordinates for boroughs of NYC to query 
BOROUGH_COORDS = {
    "MANHATTAN": (40.7831, -73.9712),
    "BROOKLYN": (40.6782, -73.9442),
    "QUEENS": (40.7282, -73.7949),
    "BRONX": (40.8448, -73.8648),
    "RICHMOND / STATEN ISLAND": (40.5795, -74.1502),
}

#set timeframe 
START_DATE = "2013-01-01"
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
        df["datetime"] = df["datetime"].dt.tz_localize(None) #localize timezone to match for joining 
        logger.info(f"{borough}: {df.shape[0]:,} rows fetched") 
        weather_dfs.append(df)
        time.sleep(1) #delay API querying 

    except Exception as e:
        logger.error(f"Failed to fetch weather for {borough}: {e}")
        print(f"Failed to fetch weather for {borough}: {e}")
        continue 

weather_df = pd.concat(weather_dfs, ignore_index=True) #combine dfs for all boroughs
#standardize borough names 
weather_df["borough"] = weather_df["borough"].astype(str).str.strip().str.upper()
#create locationtimeID for joining 
weather_df['locationtimeID'] = weather_df['borough'] + '_' + weather_df['datetime'].astype(str)
#drop duplicates with primary key 
weather_df = weather_df.drop_duplicates(subset=['locationtimeID'], keep='first')

#write to csv 
weather_df.to_csv('data/Weather.csv', index=False)
