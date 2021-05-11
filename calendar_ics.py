import icalendar
import re
import recurring_ical_events
import urllib.request
import datetime
from notion.collection import NotionDate
from update import update_row
import pandas as pd
import pytz


from work_hours import work_calendar


def find_url(s):
    link = re.search("(?P<url>https?://[^\s]+)", s) \
        if s else None
    return link.group("url") if link else None


def describe_event(event):
    res = {}
    target_time_zone = pytz.timezone('Europe/Moscow')
    start_msk = event["DTSTART"].dt
    end_msk = event["DTEND"].dt
    if isinstance(start_msk, datetime.datetime) \
            and isinstance(end_msk, datetime.datetime):
        start_msk = start_msk.astimezone(target_time_zone)
        end_msk = end_msk.astimezone(target_time_zone)
    elif (end_msk-start_msk).days == 1:
        start_msk = pd.to_datetime(start_msk)
        end_msk = None
    else:
        start_msk = pd.to_datetime(start_msk)
        end_msk = pd.to_datetime(end_msk)
    res['title'] = str(event['SUMMARY'])
    loc = str(event['LOCATION'])
    if ' ' not in loc:
        loc = loc.capitalize()
    try:
        desc = str(event['DESCRIPTION'])
    except Exception:
        desc = None
    res['description'] = desc
    link = find_url(desc)
    res['link'] = link
    res['location'] = loc if loc else None
    reminder = None  # {'unit': 'minute', 'value': 3}
    res['date'] = NotionDate(
        start_msk, end_msk, reminder=reminder)
    return res


def cal_row_key(title, dt):
    dt = pd.to_datetime(dt.start).date()
    return f'{title} {dt}'


def add_events(
    cv, rows, url, start_date=datetime.datetime.now().date(), days=90,
):
    source = 'google' if 'google' in url \
        else 'outlook' if 'forecsys' in url \
        else None
    end_date = start_date + datetime.timedelta(days=days)
    ical_string = urllib.request.urlopen(url).read()
    calendar = icalendar.Calendar.from_ical(ical_string)
    events = recurring_ical_events.of(calendar).between(start_date, end_date)
    row_dict = {cal_row_key(row.title, row.date): row
                for row in rows if row.date is not None}
    for row in rows:
        if row.source == source \
                and row.date is not None \
                and pd.to_datetime(row.date.start) >= start_date:
            row.source = None
    for event in events:
        event = describe_event(event.copy())
        if event['date'] is None:
            continue
        if source == 'outlook' \
                and pd.to_datetime(event['date'].start).date() \
                in work_calendar['vacation']:
            continue
        key = cal_row_key(event['title'], event['date'])
        finded = row_dict[key] if key in row_dict \
            else cv.collection.add_row(title=event['title'])
        update_row(finded, event)
        finded.source = source
    for row in rows:
        if row.source is None:
            row.remove()
