import os
import pandas as pd
from sodapy import Socrata
import logging
import time 

USER = " "
PASS = " "
MyAppToken = " "

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='events.log'
)
logger = logging.getLogger(__name__)

# --- Socrata client with increased timeout ---
client = Socrata(
    "data.cityofnewyork.us",
    MyAppToken,
    username=USER,
    password=PASS,
    timeout=60  # increase from default 10s
)

# --- Config ---
START_DATE = "2016-01-01T00:00:00"
END_DATE   = "2017-12-31T23:59:59"
BATCH_SIZE = 5000        # smaller batches to avoid timeout
CHUNK_SIZE = 50000       # write CSV every 50k rows
CSV_PATH   = "data/NYC_Events.csv"


# --- Helper: write chunk to CSV ---
def write_chunk_csv(buffer, write_header=True):
    if not buffer:
        return

    df = pd.DataFrame.from_records(buffer)

    # Keep only needed columns
    columns = ['event_id', 'start_date_time', 'end_date_time',
               'event_type', 'event_borough', 'event_name']
    for c in columns:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[columns]

    df = df.drop_duplicates(subset=['event_id'])
    
    # Convert datetimes
    for col in ['start_date_time', 'end_date_time']:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    df.to_csv(
        CSV_PATH,
        index=False,
        mode='a',
        header=write_header,
        date_format="%Y-%m-%d %H:%M:%S"
    )
    logger.info(f"Chunk written: {len(df)} rows")


# --- Main function ---
def get_nyc_events():
    offset = 0
    chunk_buffer = []
    write_header = True
    backoff = 5  # seconds

    while True:
        try:
            logger.info(f"Fetching offset {offset}...")
            batch = client.get(
                "bkfu-528j",
                where=f"start_date_time >= '{START_DATE}' AND start_date_time <= '{END_DATE}'",
                limit=BATCH_SIZE,
                offset=offset
            )

            if not batch:
                break

            chunk_buffer.extend(batch)
            offset += BATCH_SIZE
            logger.info(f"Buffer size: {len(chunk_buffer)}")

            # Write to CSV if buffer exceeds CHUNK_SIZE
            if len(chunk_buffer) >= CHUNK_SIZE:
                write_chunk_csv(chunk_buffer, write_header)
                write_header = False  # subsequent chunks append without header
                chunk_buffer = []

            time.sleep(0.5)  # gentle delay to avoid API throttling

        except Exception as e:
            logger.warning(f"Error at offset {offset}: {e}. Retrying in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)  # exponential backoff
            continue

    # Write any remaining records
    if chunk_buffer:
        write_chunk_csv(chunk_buffer, write_header)

    file_size_mb = os.path.getsize(CSV_PATH) / (1024 ** 2)
    logger.info(f"Events saved to {CSV_PATH} | {file_size_mb:.2f} MB")


if __name__ == "__main__":
    get_nyc_events()