import os
import pandas as pd
import numpy as np
import requests
import yaml
from datetime import datetime, timedelta

from notion_client import update_row
from update import is_equal


with open('constants.yaml') as f:
    dumped = yaml.safe_load(f)
URLS = dumped['URLS']
WORKS = dumped['work_activities']


def today_work_time(cv, rows):
    param_request = {
        'key': os.environ['rescue_key'],
        'format': 'json',
    }
    response = requests.get(URLS['RESCUE_TIME'], params=param_request)
    response = response.json()

    result = pd.DataFrame(response['rows'], columns=response['row_headers'])
    five_mins = result['Time Spent (seconds)'] / 300
    rounded = five_mins.apply(round) * 300 
    result['Time'] = rounded.apply(pd.Timedelta, args=['s'])
    return result.loc[np.isin(result.Activity, WORKS), 'Time'].sum()


def week_start(date):
    return date - timedelta(days=date.weekday())


def update_work_hours(cv, rows, rescue_key):
    work_time = today_work_time(rescue_key)
    date = datetime.today().date()
    week = week_start(date)
    kwargs = {
        'title': date.strftime('%d %B %Y, %A'),
        'date': date,
        'week': week,
        'hours': work_time.components.hours,
        'minutes': work_time.components.minutes,
    }
    finded_row = None
    for row in rows:
        if is_equal(row, kwargs):
            finded_row = row
            break
    if finded_row is None:
        finded_row = cv.collection.add_row(title=kwargs['title'])
    update_row(finded_row, kwargs)
