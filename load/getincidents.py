import pandas as pd
from sodapy import Socrata
import logging
import time
import os

#Fill in API keys 
USER = " "
PASS = " "
MyAppToken = " "


#set up logger 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='getincidents.log'
)
logger = logging.getLogger(__name__)

#client for querying from NYC city API for EMS incidents data 
#  from https://data.cityofnewyork.us/Public-Safety/EMS-Incident-Dispatch-Data/76xm-jjuj/about_data
client = Socrata(
    "data.cityofnewyork.us",
    MyAppToken,
    username=USER,
    password=PASS
)

#set timeframe and batches for querying and writing to CSV 
START_DATE = "2016-01-01T00:00:00"
END_DATE   = "2017-12-31T23:59:59"
BATCH_SIZE = 50000
CHUNK_SIZE = 500000  

def write_chunk_csv(buffer, columns, path, write_header=True):
    #function to write to the csv in batches, 
    #buffer is list of records to write, columns to read in, output path for csv, write_header used to write header for first batch
    df = pd.DataFrame.from_records(buffer)

    #cast datetime columns to pandas datetime 
    for col in ['incident_datetime', 'incident_close_datetime']:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    #ensure columns are existing 
    for c in columns:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[columns]

    #drop duplicates for incident ID primary key 
    df = df.drop_duplicates(subset=['cad_incident_id'])
    #create locationtimeID for joining
    df['locationtimeID'] = df['borough'] + '_' + df['incident_datetime'].astype(str)
    #write to csv
    df.to_csv(path, index=False, mode='a', header=write_header, date_format="%Y-%m-%d %H:%M:%S")

    logger.info(f"Chunk written to {path}: {df.shape[0]} rows")


def get_ems_incidents():
    #function to get data from API in batches and write to csv in chunks
    offset = 0 #track how many records fetched
    chunk_buffer = [] #store records for writing to csv
    chunk_num = 0 #track how many chunks written
    write_header = True #only write header for first 

    #columns needed 
    columns=['cad_incident_id', 'incident_datetime', 'incident_close_datetime',
            'borough', 'initial_call_type', 'final_call_type', 'zipcode']

    while True:
        try:
            #fetch info from API in batches 
            logger.info(f"EMS Fetching offset {offset}...")
            batch = client.get("76xm-jjuj", #code for this dataset
                     where=f"incident_datetime >= '{START_DATE}' AND incident_datetime <= '{END_DATE}'", 
                     limit=BATCH_SIZE, offset=offset)
            logger.info(f"EMS Fetched {len(batch)} rows")
            if not batch: #when nothing to process 
                break

            chunk_buffer.extend(batch) #add batch to buffer 
            offset += BATCH_SIZE #increment offset 
            logger.info(f"EMS Buffer size: {len(chunk_buffer)}")
            time.sleep(0.5) #rest time

            #write chunk to csv when buffer is larger than chunk size 
            if len(chunk_buffer) >= CHUNK_SIZE:
                write_chunk_csv(chunk_buffer, columns, "data/EMS_Incidents.csv", write_header)
                write_header = False  #only write header for first 
                chunk_buffer = []
                chunk_num += 1

        except Exception as e: #error handling 
            logger.warning(f"EMS Error at offset {offset}: {e}. Retrying in 10s...")
            time.sleep(10)
            continue

    #write remaining records
    if chunk_buffer:
        write_chunk_csv(chunk_buffer, columns, "data/EMS_Incidents.csv", write_header)

    logger.info(f"EMS Done. CSV saved to data/EMS_Incidents.csv")


if __name__ == "__main__":
    get_ems_incidents()