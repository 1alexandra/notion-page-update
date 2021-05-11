import os
import sys
import yaml
import traceback
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from socket import gethostname

from notion_client import get_client
from notion_client import get_cv_rows
from notion_client import get_last_date, update_last_date
from youtube import get_youtube_urls
from rss import SportsRSS, MangaRSS, SeriesRSS, YouTubeRSS
from update import update, log_result
from tody_killer import update_tody, update_private
from weather import update_weather
from work_hours import update_work_hours
from plot_work_hours import plot_work_hours
from calendar_ics import add_events

minutes = 120
if len(sys.argv) == 2:
    MODE = 'heroku'
    minutes = int(sys.argv[1])
else:
    MODE = 'local'

with open('constants.yaml') as f:
    dumped = yaml.safe_load(f)
URLS = dumped['URLS']
sched = BlockingScheduler()


def processing(client):
    cv, rows = get_cv_rows(client, URLS['WHAT_TO_WATCH'])
    _, rows_yt = get_cv_rows(client, URLS['YOUTUBE_LIST'])
    _, rows_td = get_cv_rows(client, URLS['TODY_KILLER'])
    _, rows_pr = get_cv_rows(client, URLS['PRIVATE'])
    cv_w, rows_w = get_cv_rows(client, URLS['WEATHER'])
    cv_h, rows_h = get_cv_rows(client, URLS['WORK_HOURS'])
    last_date = get_last_date(rows)
    update(cv, rows, MangaRSS(last_date), False)
    update(cv, rows, SportsRSS(URLS['BLOG_RSS'], last_date), False)
    try:
        update(cv, rows, SeriesRSS(last_date), False)
    except Exception:
        pass
    for url in get_youtube_urls(rows_yt):
        update(cv, rows, YouTubeRSS(url, last_date), True)
    update_last_date(rows)
    # update_tody(rows_td)
    # update_private(rows_pr)
    # update_weather(cv_w, rows_w, key_num=2)
    update_work_hours(cv_h, rows_h)

    for source in ['google', 'outlook']:
        cv, rows = get_cv_rows(client, URLS['CALENDAR'])
        add_events(cv, rows, os.environ[f'{source}_ics'])
    if gethostname() == 'LAPTOP-6MEALABP':
        cv_h, rows_h = get_cv_rows(client, URLS['WORK_HOURS'])
        plot_work_hours(rows_h)


@sched.scheduled_job('interval', minutes=minutes)
def main():
    zone = timezone(timedelta(hours=3))
    tb = 'Success'
    start = datetime.now(tz=zone)
    client = get_client()
    try:
        print('PROCESSING')
        processing(client)
    except Exception:
        print('EXCEPTION')
        tb = traceback.format_exc()
    finally:
        print('LOGGING')
        cv_log, rows_log = get_cv_rows(client, URLS['LOGS_TABLE'])
        finish = datetime.now(tz=zone)
        log_result(cv_log, rows_log, tb, start, finish, zone)


if __name__ == "__main__":
    main()
    if MODE == 'heroku':
        sched.start()
