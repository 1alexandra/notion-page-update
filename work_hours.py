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
with open('work_days.yaml') as f:
	work_calendar = yaml.safe_load(f)
for key in work_calendar:
	work_calendar[key] = [pd.to_datetime(dt).date() for dt in work_calendar[key]]


def get_work_time(date):
    param_request = {
        'key': os.environ['rescue_key'],
        'format': 'json',
        'restrict_begin': date,
        'restrict_end': date,
    }
    response = requests.get(URLS['RESCUE_TIME'], params=param_request)
    response = response.json()

    result = pd.DataFrame(response['rows'], columns=response['row_headers'])
    five_mins = result['Time Spent (seconds)'] / 300
    rounded = five_mins.apply(round) * 300
    result['Time'] = rounded.apply(pd.Timedelta, args=['s'])
    work_result = result[np.isin(result.Activity, WORKS)]
    if len(work_result) > 0:
        return work_result.Time.sum()
    return pd.Timedelta(days=0)


def week_start(date):
    return date - timedelta(days=date.weekday())


def month_start(date):
    return date - pd.Timedelta(days=date.day-1)


def update_work_hours(cv, rows, date=None, log=False):
    date = date if date is not None else datetime.today().date()
    if date.weekday() >= 5 and date not in work_calendar['work'] \
    		or date in work_calendar['holiday'] \
    		or date in work_calendar['vacation']:
        return
    week = week_start(date)
    work_time = get_work_time(date)
    kwargs = {
        'title': date.strftime('%d %B %Y, %A'),
        'date': date,
        'week': week,
        'hours': work_time.components.hours or 0,
        'minutes': work_time.components.minutes or 0,
    }
    if log:
        print(kwargs)
    finded_row = None
    for row in rows:
        if is_equal(row, kwargs):
            finded_row = row
            break
    if finded_row is None:
        finded_row = cv.collection.add_row(title=kwargs['title'])
    update_row(finded_row, kwargs)
