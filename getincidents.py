import pandas as pd
from sodapy import Socrata
import logging
import time
import os
import pyarrow

USER = " "
PASS = " "
MyAppToken = " "


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='getincidents.log'
)
logger = logging.getLogger(__name__)

# Socrata client
client = Socrata(
    "data.cityofnewyork.us",
    MyAppToken,  # replace with your token
    username=USER,
    password=PASS
)

# Config
START_DATE = "2016-01-01T00:00:00"
END_DATE   = "2017-12-31T23:59:59"
BATCH_SIZE = 50000
CHUNK_SIZE = 500000   # write to disk every 500k rows


def _write_chunk_csv(buffer, columns, datetime_cols, path, write_header=True):
    """Convert buffer to DataFrame, cast types, write to CSV."""
    df = pd.DataFrame.from_records(buffer)

    # Cast datetime columns
    if datetime_cols:
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

    # Ensure all columns exist and order is consistent
    for c in columns:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[columns]

    df = df.drop_duplicates(subset=['cad_incident_id'])
    # Write CSV (append mode after first chunk)
    df.to_csv(
        path,
        index=False,
        mode='a',
        header=write_header,
        date_format="%Y-%m-%d %H:%M:%S"
    )

    logger.info(f"Chunk written to {path}: {df.shape[0]} rows")


def paginate_to_csv(dataset_id, where_clause, label, columns, output_path, datetime_cols=None):
    """Fetches dataset in batches and writes to CSV in chunks."""
    offset = 0
    chunk_buffer = []
    chunk_num = 0
    write_header = True

    while True:
        try:
            logger.info(f"[{label}] Fetching offset {offset}...")
            batch = client.get(
                dataset_id,
                where=where_clause,
                limit=BATCH_SIZE,
                offset=offset
            )
            logger.info(f"[{label}] Fetched {len(batch)} rows")
            if not batch:
                break

            chunk_buffer.extend(batch)
            offset += BATCH_SIZE
            logger.info(f"[{label}] Buffer size: {len(chunk_buffer)}")
            time.sleep(0.5)

            # Write chunk if buffer exceeds CHUNK_SIZE
            if len(chunk_buffer) >= CHUNK_SIZE:
                _write_chunk_csv(chunk_buffer, columns, datetime_cols, output_path, write_header)
                write_header = False  # subsequent chunks append without header
                chunk_buffer = []
                chunk_num += 1

        except Exception as e:
            logger.warning(f"[{label}] Error at offset {offset}: {e}. Retrying in 10s...")
            time.sleep(10)
            continue

    # Write any remaining records
    if chunk_buffer:
        _write_chunk_csv(chunk_buffer, columns, datetime_cols, output_path, write_header)

    logger.info(f"[{label}] Done. CSV saved to {output_path}")


def get_ems_incidents():
    """Fetch EMS incidents and save to CSV."""
    paginate_to_csv(
        dataset_id="76xm-jjuj",
        where_clause=f"incident_datetime >= '{START_DATE}' AND incident_datetime <= '{END_DATE}'",
        label="EMS",
        columns=[
            'cad_incident_id', 'incident_datetime', 'incident_close_datetime',
            'borough', 'initial_call_type', 'final_call_type', 'zipcode'
        ],
        output_path="data/EMS_Incidents.csv",
        datetime_cols={
            'incident_datetime': None,
            'incident_close_datetime': None
        }
    )

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    get_ems_incidents()