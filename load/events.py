import os
import pandas as pd
from sodapy import Socrata
import logging
import time 

#API keys 
USER = " "
PASS = " "
MyAppToken = " "

#create log file 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='events.log'
)
logger = logging.getLogger(__name__)

#client for querying from NYC city API for historical events data with keys 
#  from https://data.cityofnewyork.us/City-Government/NYC-Permitted-Event-Information-Historical/bkfu-528j/about_data
client = Socrata(
    "data.cityofnewyork.us",
    MyAppToken,
    username=USER,
    password=PASS
)

#set timeframe and batches for querying to abide by API limits and writing to CSV to work with memory  
START_DATE = "2016-01-01T00:00:00"
END_DATE = "2017-12-31T23:59:59"
BATCH_SIZE = 5000   
CHUNK_SIZE = 50000 


def write_chunk_csv(buffer, write_header=True):
    #function to help write to the csv in batches
    # buffer is list of records to write, write_header used to write header for first batch
    if not buffer:
        return

    df = pd.DataFrame.from_records(buffer)

    #columns to read in 
    columns = ['event_id', 'start_date_time', 'end_date_time',
               'event_type', 'event_borough', 'event_name']
    for c in columns:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[columns]

    #avoid duplicate event IDs
    df = df.drop_duplicates(subset=['event_id'])
    
    #convert datetimes 
    for col in ['start_date_time', 'end_date_time']:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    #standardize borough names 
    df["event_borough"] = df["event_borough"].astype(str).str.strip().str.upper()
    #crate locationtimeID for joining 
    df['locationtimeID'] = df['event_borough'] + '_' + df['start_date_time'].astype(str)

    #write chunk to csv
    df.to_csv(
        "data/NYC_Events.csv", index=False, mode='a', header=write_header,
        date_format="%Y-%m-%d %H:%M:%S"
    )
    logger.info(f"Chunk written: {len(df)} rows")


def get_nyc_events():
    #function to query events data from API in batches and write to csv in chunks
    offset = 0 #used in pagination to track how many records have been fetched
    chunk_buffer = [] #temporary storage for records before writing to csv
    write_header = True #only write header for first chunk
    backoff = 5  #pause in between API calls 

    while True:
        try:
            #try fetching from API with current offset
            logger.info(f"Fetching offset {offset}...")
            batch = client.get("bkfu-528j", #code for specific dataset 
                where=f"start_date_time >= '{START_DATE}' AND start_date_time <= '{END_DATE}'",
                limit=BATCH_SIZE, offset=offset)

            if not batch: #when nothing else to process 
                break

            chunk_buffer.extend(batch) #add specific batch to buffer
            offset += BATCH_SIZE #increment offset for next batch
            logger.info(f"Buffer size: {len(chunk_buffer)}")

            #write to CSV once buffer is bigger than size of chunks
            if len(chunk_buffer) >= CHUNK_SIZE:
                write_chunk_csv(chunk_buffer, write_header)
                write_header = False  #only first needs header
                chunk_buffer = []

            time.sleep(0.5) #delay for API limits 

        except Exception as e: #error handling 
            logger.warning(f"Error at offset {offset}: {e}. Retrying in {backoff}s...")
            time.sleep(backoff) #sleep and try again
            backoff = min(backoff * 2, 60)  #wait exponentially more time, up to 60s
            continue

    #write remaining records 
    if chunk_buffer:
        write_chunk_csv(chunk_buffer, write_header)

    logger.info(f"Events saved to data/NYC_Events.csv")


if __name__ == "__main__":
    get_nyc_events()