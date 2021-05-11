import yaml

from datetime import datetime, timedelta

import pandas as pd

from soup import get_soup

from calendar_ics import find_url


with open('constants.yaml') as f:
    dumped = yaml.safe_load(f)
URLS = dumped['URLS']


class BaseRSS:
    def __init__(self, url, last_date, item_name='item'):
        self.soup = get_soup(url)
        self.item = item_name
        self.last_date = last_date

    def __iter__(self):
        for el in reversed(self.soup.find_all(self.item)):
            row = {
                'title': self.get_title(el),
                'link': self.get_link(el),
                'season': self.get_season(el),
                'episode': self.get_episode(el),
                'date': self.get_date(el)
            }
            if row['date'] >= self.last_date:
                yield row

    def get_title(self, el):
        try:
            return el.title.text
        except Exception:
            return ''

    def get_link(self, el):
        try:
            link = el.link.get('href')
            assert link
            return link
        except Exception:
            try:
                return find_url(el.text)
            except Exception:
                return ''

    def get_season(self, el):
        return None

    def get_episode(self, el):
        return None

    def get_date(self, el):
        return datetime.now().date()


def savety(method):
    def savety_method(self, *args, **kwargs):
        try:
            a = method(self, *args, **kwargs)
        except Exception:
            parent_method = getattr(self.parent, method.__name__)
            a = parent_method(*args, **kwargs)
        return a
    return savety_method


class MangaRSS(BaseRSS):
    def __init__(self, last_date):
        super().__init__(URLS['MANGA_RSS'], last_date)
        self.parent = BaseRSS(URLS['MANGA_RSS'], last_date)

    @savety
    def get_title(self, el):
        title = el.title.text.split(' - ')[0]
        return ' '.join(title.split(' ')[1:-1])

    @savety
    def get_link(self, el):
        return el.guid.text

    @savety
    def get_season(self, el):
        title = el.title.text.split(' - ')[0]
        return int(title.split(' ')[-1])

    @savety
    def get_episode(self, el):
        episode = el.title.text.split(' - ')[1]
        return int(episode.split(' ')[0])

    @savety
    def get_date(self, el):
        return datetime.strptime(el.pubdate.text[:-6],
                                 '%a, %d %b %Y %H:%M:%S').date()


class SeriesRSS(BaseRSS):
    def __init__(self, last_date):
        super().__init__(URLS['SERIES_ON_RSS'], last_date)
        self.translation_time = timedelta(days=1)
        self.parent = BaseRSS(URLS['SERIES_ON_RSS'], last_date)

    @savety
    def get_title(self, el):
        return ' '.join(el.title.text.split(' ')[:-1])

    @savety
    def get_season(self, el):
        episode = el.title.text.split(' ')[-1]
        try:
            s = int(episode[1:].split('e')[0])
        except Exception:
            return None
        return s

    @savety
    def get_episode(self, el):
        episode = el.title.text.split(' ')[-1]
        try:
            e = int(episode[1:].split('e')[1])
        except Exception:
            return None
        return e

    @savety
    def get_date(self, el):
        date = datetime.strptime(el.pubdate.text[:-6],
                                 '%a, %d %b %Y %H:%M:%S').date()
        return date + self.translation_time


class YouTubeRSS(BaseRSS):
    def __init__(self, url, last_date):
        super().__init__(url, last_date, 'entry')
        self.parent = BaseRSS(url, last_date, 'entry')

    @savety
    def get_title(self, el):
        return el.author.find('name').text + ': ' + el.title.text

    @savety
    def get_date(self, el):
        return datetime.strptime(el.published.text[:10],
                                 '%Y-%m-%d').date()


class SportsRSS(BaseRSS):
    def __init__(self, url, last_date):
        super().__init__(url, last_date)
        self.parent = BaseRSS(url, last_date)

    @savety
    def get_date(self, el):
        return pd.to_datetime(el.pubdate.text).date()

    @savety
    def get_link(self, el):
        return find_url(el.text)
