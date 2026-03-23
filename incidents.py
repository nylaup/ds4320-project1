
import pandas as pd 

#Incidents info file downloaded from https://data.cityofnewyork.us/Public-Safety/EMS-Incident-Dispatch-Data/76xm-jjuj/about_data
#  selecting information from specific time period 
df = pd.read_csv("EMS_Incident_Dispatch_Data_20260322.csv")

incidents = df.loc[:,['CAD_INCIDENT_ID', 'INCIDENT_DATETIME', 'BOROUGH']]
incidents['INCIDENT_DATETIME'] = pd.to_datetime(incidents['INCIDENT_DATETIME'], format="%m/%d/%Y %I:%M:%S %p")

#create locationtime using location and time
incidents['LocationTimeID'] = incidents['BOROUGH'] + "_" + incidents['INCIDENT_DATETIME'].astype(str)

incidents.to_csv('Incidents.csv')