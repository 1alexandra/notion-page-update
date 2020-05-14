import yaml

from datetime import datetime, timedelta

from soup import get_soup


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
        return el.title.text

    def get_link(self, el):
        return el.link.get('href')

    def get_season(self, el):
        return None

    def get_episode(self, el):
        return None

    def get_date(self, el):
        return datetime.now().date()


class MangaRSS(BaseRSS):
    def __init__(self, last_date):
        super().__init__(URLS['MANGA_RSS'], last_date)

    def get_title(self, el):
        title = el.title.text.split(' - ')[0]
        return ' '.join(title.split(' ')[1:-1])

    def get_link(self, el):
        return el.guid.text

    def get_season(self, el):
        title = el.title.text.split(' - ')[0]
        return int(title.split(' ')[-1])

    def get_episode(self, el):
        episode = el.title.text.split(' - ')[1]
        return int(episode.split(' ')[0])

    def get_date(self, el):
        return datetime.strptime(el.pubdate.text[:-6],
                                 '%a, %d %b %Y %H:%M:%S').date()


class SeriesRSS(BaseRSS):
    def __init__(self, last_date):
        super().__init__(URLS['SERIES_ON_RSS'], last_date)
        self.translation_time = timedelta(days=1)

    def get_title(self, el):
        return ' '.join(el.title.text.split(' ')[:-1])

    def get_season(self, el):
        episode = el.title.text.split(' ')[-1]
        try:
            s = int(episode[1:].split('e')[0])
        except Exception:
            return None
        return s

    def get_episode(self, el):
        episode = el.title.text.split(' ')[-1]
        return int(episode[1:].split('e')[1])

    def get_date(self, el):
        date = datetime.strptime(el.pubdate.text[:-6],
                                 '%a, %d %b %Y %H:%M:%S').date()
        return date + self.translation_time


class YouTubeRSS(BaseRSS):
    def __init__(self, url, last_date):
        super().__init__(url, last_date, 'entry')

    def get_title(self, el):
        return el.author.find('name').text + ': ' + el.title.text

    def get_date(self, el):
        return datetime.strptime(el.published.text[:10],
                                 '%Y-%m-%d').date()
