import pandas as pd 
import duckdb
import logging
import time

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    filename='dem.log'
)
logger = logging.getLogger(__name__)

try: 
    #Neighborhood demographics file downloaded from https://www.furmancenter.org/data-tools-resources/data-tools-data-downloads/ 
    #  then converted from xlsx to csv
    logger.info("Reading demographics data from CSV...")
    df = pd.read_csv("data/Neighorhood_Indicators_CoreDataDownload_2025-05-15.csv")

    #take relevant columns 
    neighborhood = df.loc[:,['region_name', 'year', 'crime_viol_rt', 'hh_inc_med_adj', 
        'hh_u18_pct', 'pop_65p_pct', 'pop_num']]

    #starting with 2016 data, so take data from just one year 
    neighborhood['year'] = pd.to_numeric(neighborhood['year'], errors='coerce')
    neighborhood = neighborhood[neighborhood['year'] == 2016]

    logger.info(f"Converting data types")

    #drop unneccesary characters to convert to floats 
    neighborhood["hh_inc_med_adj"] = (neighborhood["hh_inc_med_adj"].str.replace("$", "", regex=False)
                                      .str.replace(",", "", regex=False).astype(float))
    neighborhood["hh_u18_pct"] = neighborhood["hh_u18_pct"].str.replace("%", "", regex=False).astype(float)
    neighborhood["pop_65p_pct"] = neighborhood["pop_65p_pct"].str.replace("%", "", regex=False).astype(float)
    neighborhood["pop_num"] = neighborhood["pop_num"].str.replace(",", "", regex=False).astype(float)

    #only keep one row for each neighborhood and year
    neighborhood = neighborhood.drop_duplicates(subset=['region_name', 'year'], keep='first')
    #standardize neighborhood names
    neighborhood["region_name"] = neighborhood["region_name"].astype(str).str.strip().str.upper()
        #change staten island name to match incidents table
    neighborhood["region_name"] = (neighborhood["region_name"].str.replace("STATEN ISLAND","RICHMOND / STATEN ISLAND"))

    #write to csv file 
    neighborhood.to_csv('data/Demographics.csv', index=False)
    logger.info(f"Created csv file for demographics data")

except Exception as e:
        logger.error(f"Failed to read demographics data: {e}")
        print(f"Failed to read demographics data: {e}")
