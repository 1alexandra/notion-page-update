import sys
import yaml
import traceback
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.blocking import BlockingScheduler

from notion_client import get_client, get_last_date, update_last_date
from youtube import get_youtube_urls
from rss import MangaRSS, SeriesRSS, YouTubeRSS
from update import update, log_result
from tody_killer import update_tody, update_private

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
    cv = client.get_collection_view(URLS['WHAT_TO_WATCH'])
    rows = cv.default_query().execute()
    cv_yt = client.get_collection_view(URLS['YOUTUBE_LIST'])
    rows_yt = cv_yt.default_query().execute()
    cv_td = client.get_collection_view(URLS['TODY_KILLER'])
    rows_td = cv_td.default_query().execute()
    cv_pr = client.get_collection_view(URLS['PRIVATE'])
    rows_pr = cv_pr.default_query().execute()
    last_date = get_last_date(rows)
    update(cv, rows, MangaRSS(last_date), False)
    update(cv, rows, SeriesRSS(last_date), False)
    for url in get_youtube_urls(rows_yt):
        update(cv, rows, YouTubeRSS(url, last_date), True)
    update_last_date(rows)
    update_tody(rows_td)
    update_private(rows_pr)


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
        cv_log = client.get_collection_view(URLS['LOGS_TABLE'])
        finish = datetime.now(tz=zone)
        log_result(cv_log, tb, start, finish, zone)


if __name__ == "__main__":
    main()
    if MODE == 'heroku':
        sched.start()
