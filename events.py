
import pandas as pd 

#Events info file downloaded from https://data.cityofnewyork.us/City-Government/NYC-Permitted-Event-Information-Historical/bkfu-528j/about_data
#  selecting information from specific time period 
df = pd.read_csv("NYC_Permitted_Event_Information_-_Historical_20260322.csv")

events = df.loc[:,['Event ID', 'Start Date/Time', 'End Date/Time', 'Event Type', 'Event Borough']]

#convert start and end times to pd datetime
events['Start Date/Time'] = pd.to_datetime(events['Start Date/Time'], format="%m/%d/%Y %I:%M:%S %p")
events['End Date/Time'] = pd.to_datetime(events['End Date/Time'], format="%m/%d/%Y %I:%M:%S %p")

events.to_csv('Events.csv')