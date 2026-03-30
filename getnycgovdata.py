import pandas as pd
from sodapy import Socrata
import logging
import time
import os
import pyarrow

USER = "mge9dn@virginia.edu"
PASS = "NnU030605030605"
MyAppToken = "okyJkohbe1GifeURdORp8xuQm"

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='getnycdata.log'
)
logger = logging.getLogger(__name__)

client = Socrata(
    "data.cityofnewyork.us",
    MyAppToken,
    username=USER,
    password=PASS
)

#Choose 4 years for both datasets 
START_DATE = "2016-01-01T00:00:00"
END_DATE   = "2019-12-31T23:59:59"
BATCH_SIZE = 50000
CHUNK_SIZE = 500000   # write to disk every 500k rows


def paginate_to_parquet(dataset_id, where_clause, label, columns, output_path, datetime_cols=None):
    """Fetches in batches, writes to parquet in chunks"""
    offset = 0
    chunk_buffer = []
    chunk_num = 0
    part_files = []

    while True:
        try:
            logger.info(f"[{label}] Fetching offset {offset}...")
            batch = client.get(
                dataset_id,
                where=where_clause,
                limit=BATCH_SIZE,
                offset=offset
            )
            print(f"Success — {len(batch)} rows returned")
            if not batch:
                break

            chunk_buffer.extend(batch)
            offset += BATCH_SIZE
            logger.info(f"[{label}] Buffer size: {len(chunk_buffer)}")
            time.sleep(0.5)

            # Write chunk to disk and clear buffer
            if len(chunk_buffer) >= CHUNK_SIZE:
                part_path = f"data/{label}_part{chunk_num}.parquet"
                _write_chunk(chunk_buffer, columns, datetime_cols, part_path)
                part_files.append(part_path)
                chunk_buffer = []
                chunk_num += 1

        except Exception as e:
            logger.warning(f"[{label}] Error at offset {offset}: {e}. Retrying in 10s...")
            time.sleep(10)
            continue

    # Write any remaining records
    if chunk_buffer:
        part_path = f"data/{label}_part{chunk_num}.parquet"
        _write_chunk(chunk_buffer, columns, datetime_cols, part_path)
        part_files.append(part_path)

    # Combine all parts into final parquet
    logger.info(f"[{label}] Combining {len(part_files)} parts...")
    combined = pd.concat([pd.read_parquet(f) for f in part_files], ignore_index=True)
    combined.to_parquet(output_path, index=False, engine='pyarrow')

    # Clean up part files
    for f in part_files:
        os.remove(f)

    logger.info(f"[{label}] Done. {combined.shape[0]} rows saved to {output_path}")

def _write_chunk(buffer, columns, datetime_cols, path):
    """Convert buffer to DataFrame, cast types, write parquet."""
    df = pd.DataFrame.from_records(buffer)

    # Keep only needed columns that exist
    existing_cols = [c for c in columns if c in df.columns]
    df = df[existing_cols]

    if datetime_cols:
        for col in datetime_cols.items():
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

    df.to_parquet(path, index=False, engine='pyarrow')
    logger.info(f"Chunk written to {path}: {df.shape[0]} rows")


def get_ems_incidents():
    paginate_to_parquet(
        dataset_id="76xm-jjuj",
        where_clause=f"incident_datetime >= '{START_DATE}' AND incident_datetime <= '{END_DATE}'",
        label="EMS",
        columns=['cad_incident_id', 'incident_datetime', 'incident_close_datetime',
                 'borough', 'initial_call_type', 'final_call_type', 'zipcode'],
        output_path="data/EMS_Incidents.parquet",
        datetime_cols={
            'incident_datetime': "%m/%d/%Y %I:%M:%S %p",
            'incident_close_datetime': "%m/%d/%Y %I:%M:%S %p"
        }
    )


if __name__ == "__main__":
    get_ems_incidents()




