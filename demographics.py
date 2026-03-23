import pandas as pd 

#Neighborhood demographics file downloaded from https://www.furmancenter.org/data-tools-resources/data-tools-data-downloads/ 
#  then converted from xlsx to csv
df = pd.read_csv("Neighorhood_Indicators_CoreDataDownload_2025-05-15.csv")

neighborhood = df.loc[:,['region_name', 'region_type', 'year', 'crime_viol_rt', 'hh_inc_med_adj', 
    'hh_u18_pct', 'pop_65p_pct', 'pop_num']]

neighborhood = neighborhood[neighborhood['year']=='2023']

neighborhood.to_csv('Demographics.csv')