'''
This script edits the default-schedule.csv file
to account for Daylight Savings Time and user edits.

It takes Local Time values and updates the UTC and Cron values.

Thus one only needs to find the best local time 
(when the store's order page is active)
without having to worry about timezone conversion accuracy.

A Github Actions workflow should be set to activate once a day, and
on every pushed commit that edits the default-schedule.csv file
'''


# ======================================================= #
# Step 1: Import libraries and define necessary functions #
# ======================================================= #

import pytz
from datetime import datetime
import pandas as pd


# Function to localize each local time string
# returns a datetime object with timezone included
def init_local(tz, t):
	timezone = pytz.timezone(tz)
	aware_dt = datetime.now(timezone).replace(hour=int(t[:2]), minute=int(t[3:]))
	return aware_dt


# Function to get UTC offset (time difference between local time and UTC)
# in string format "[+-]hh:mm"
# DST offset, if applicable, has already been added
def utc_offset(tz, t):
	hhmm = init_local(tz, t).strftime("%z")
	hh_mm = hhmm[:3] + ":" + hhmm[3:]
	return hh_mm
	

# Function to convert local time to UTC equivalent,
# returns in string format "hh:mm"
def utc_time(tz, t):
	utc_dt = init_local(tz, t).astimezone(pytz.utc)
	utc_t = utc_dt.strftime("%H:%M")
	return utc_t
	

# Function to render converted UTC time in cron format
# returns a string "mm hh * * *"
def cron_time(tz, t):
	utc_dt = init_local(tz, t).astimezone(pytz.utc)
	cron = utc_dt.strftime("%M %H * * *")
	return cron


# Function to adjust start and stop values of the Pandas DataFrame index
def reset_index(n):
    df.index = pd.RangeIndex(
        start=n, stop=(len(df.index) + n), step=1
    )

	

# ======================================================= #
# Step 2: Import CSV data into DataFrame and clean it     #
# ======================================================= #

'''
	Column headers
	
     0	     1	      2	       3    4         5              6          7 
| [index] | Code | Timezone | UTC | Cron | UTC Offset | Local Time | Library |
#																			'''


df = pd.read_csv("default-schedule.csv", index_col=0)


reset_index(0)


# List comprehension returns series of values (list) after 
# chosen function iterates through temporary DataFrame extract
def list_c(f):
    return pd.Series([f(row[0], row[1]) for row in zip(df["Timezone"], df["Local Time"])])

df["UTC"] = list_c(utc_time)
df["Cron"] = list_c(cron_time)
df["UTC Offset"] = list_c(utc_offset)


reset_index(1)



# ======================================================= #
# Step 3: Export new data to overwrite file               #
# ======================================================= #

df.to_csv("default-schedule.csv")
