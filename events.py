import os
import pandas as pd
from sodapy import Socrata
import logging

USER = " "
PASS = " "
MyAppToken = " "

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='events.log'
)
logger = logging.getLogger(__name__)

client = Socrata(
    "data.cityofnewyork.us",
    MyAppToken,
    username=USER,
    password=PASS
)

START_DATE = "2016-01-01T00:00:00"
END_DATE   = "2019-12-31T23:59:59"


def get_nyc_events():
    try:
        logger.info("Fetching NYC Events data...")
        results = client.get(
            "bkfu-528j",
            where=f"start_date_time >= '{START_DATE}' AND start_date_time <= '{END_DATE}'",
            limit=500000  # well above expected count
        )

        df = pd.DataFrame.from_records(results)
        logger.info(f"Fetched {df.shape[0]:,} rows")

        df = df[['event_id', 'start_date_time', 'end_date_time',
                 'event_type', 'event_borough', 'event_name']]

        df['start_date_time'] = pd.to_datetime(df['start_date_time'])
        df['end_date_time']   = pd.to_datetime(df['end_date_time'])

        df.to_parquet('data/NYC_Events.parquet', index=False)

        file_size_mb = os.path.getsize('data/NYC_Events.parquet') / (1024 ** 2)
        logger.info(f"Events saved: {df.shape[0]:,} rows | {df.shape[1]} cols | {file_size_mb:.2f} MB")

    except Exception as e:
        logger.error(f"Error fetching Events data: {e}")
        print(f"Error fetching Events data: {e}")


if __name__ == "__main__":
    get_nyc_events()