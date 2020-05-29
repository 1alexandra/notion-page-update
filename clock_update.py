import sys
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler

from notion_client import get_client, get_last_date, update_last_date
from youtube import get_youtube_urls
from rss import MangaRSS, SeriesRSS, YouTubeRSS
from update import update

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


@sched.scheduled_job('interval', minutes=240)
def main():
    client = get_client()
    cv = client.get_collection_view(URLS['WHAT_TO_WATCH'])
    rows = cv.default_query().execute()
    cv_yt = client.get_collection_view(URLS['YOUTUBE_LIST'])
    rows_yt = cv_yt.default_query().execute()
    last_date = get_last_date(rows)
    update(cv, rows, MangaRSS(last_date), False)
    update(cv, rows, SeriesRSS(last_date), False)
    for url in get_youtube_urls(rows_yt):
        update(cv, rows, YouTubeRSS(url, last_date), True)
    update_last_date(rows)


main()
if MODE == 'heroku':
    sched.start()
