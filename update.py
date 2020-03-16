from notion.client import NotionClient
from notion.block import VideoBlock

COLL_URL = "https://www.notion.so/zhuav/0a23057cdbc141d8b20667573857d8be?v=9154c0f034bf45c3b1269e9d8a3cd0b2"
COLL_YOUTUBE_URL = "https://www.notion.so/zhuav/3745c12264d7475f8cad58c789cfaf72?v=74df3a81051a4a19aca2de91d381ee71"

def get_client(token_filename = 'token.txt'):
    with open(token_filename, 'r') as file:
        token = file.read()
    return NotionClient(token_v2=token)

def get_rows(client, coll_url = COLL_URL):
    cv = client.get_collection_view(coll_url)
    return cv.default_query().execute(), cv

def update_row(row, kwargs):
    print('Updating:', row.title)
    if 'episode' in kwargs.keys():
        row.episode = kwargs['episode']
    if 'season' in kwargs.keys():
        row.season = kwargs['season']
    if 'link' in kwargs.keys():
        row.link = kwargs['link']
    if 'when' in kwargs.keys():
        row.when = kwargs['when']
    
import datetime

LAST_DATE = None

def get_last_date(client, coll_url = COLL_URL):
    global LAST_DATE
    if LAST_DATE is None:  
        rows, cv = get_rows(client, coll_url)
        for row in rows:
            if row.title == 'last_date.txt':
                LAST_DATE = row.date.start
                break
    return LAST_DATE
        
def update_last_date(client, coll_url = COLL_URL):
    rows, cv = get_rows(client, coll_url)
    today = datetime.datetime.now().date()
    for row in rows:
        if row.title == 'last_date.txt':
            row.date = today
        elif row.date is not None and row.date.start < today and row.seen == 'yes':
            row.remove()
        
from bs4 import BeautifulSoup
import requests

def get_soup(url):
    session_requests = requests.session()
    result = session_requests.get(url, headers = dict(referer = url))
    return BeautifulSoup(result.content, features="lxml")

def update(sourse_urls, client, item_name, get_date, get_content, get_video = None, coll_url = COLL_URL):
    last_date = get_last_date(client, coll_url)
    rows, cv = get_rows(client, coll_url)
    added_names = []
    for sourse_url in sourse_urls:
        soup = get_soup(sourse_url)
        for item in reversed(soup.find_all(item_name)):
            cur_date = get_date(item)
            if last_date > cur_date:
                continue
            name, kwargs = get_content(item)
            if name in added_names:
                continue
            finded_row = None
            for row in rows:
                if row.title == name:
                    finded_row = row
                    break
            if finded_row is not None and (
                finded_row.date is not None 
                or 
                finded_row.season is not None and
                'season' in kwargs.keys() and 
                int(finded_row.season) > kwargs['season'] 
                or
                finded_row.episode is not None and
                'episode' in kwargs.keys() and
                int(finded_row.episode) > kwargs['episode']
            ):
                continue
            if finded_row is None:
                finded_row = cv.collection.add_row(title=name)
                added_names.append(name)
                if get_video is not None:
                    video = finded_row.children.add_new(VideoBlock)
                    video.set_source_url(get_video(item))
            update_row(finded_row, kwargs)
            finded_row.date = cur_date

def get_youtube_info(url):
    tag = None
    tags = ['channel', 'playlist', 'user']
    for t in tags:
        if t in url:
            tag = t
            break
    sep = '=' if tag == 'playlist' else '/'
    id_ = url.split(sep)[-1]
    postfix = '_id' if tag != 'user' else ''
    xml = 'https://www.youtube.com/feeds/videos.xml?' + tag + '=' + postfix + id_
    soup = get_soup(xml)
    name = soup.find('name').text 
    rss = get_youtube_rss(id_, tag)
    return name, tag, rss

def get_youtube_urls(coll_yt = COLL_YOUTUBE_URL):
    rows_yt, cv_yt = get_rows(client, coll_yt)
    urls = []
    for row in rows_yt:
        if row.rss == '':
            row.name, row.tag, row.rss = get_youtube_info(row.link)
        urls.append(row.rss)
    return urls            

client = get_client()

print('updating manga list')

def get_date(item): 
    return datetime.datetime.strptime(item.pubdate.text[:-6],
                                      '%a, %d %b %Y %H:%M:%S').date()
def get_content(item):
    name, *episode = item.title.text.split(' - ') 
    name = name.split(' ')
    season = int(name[-1])
    name = ' '.join(name[1:-1])
    episode = int(episode[0].split(' ')[0])
    link = item.guid.text
    return name, {'episode' : episode, 
                  'season' : season, 
                  'link' : link
                 }

update(['https://grouple.co/user/rss/1667979'], 
       client, 'item', get_date, get_content)

print('updating serials list')

def get_date(item): 
    return (datetime.datetime.strptime(item.pubdate.text[:-6], 
                                       '%a, %d %b %Y %H:%M:%S').date() 
            + datetime.timedelta(days=1))

def get_content(item):
    *name, episode = item.title.text.split(' ')
    season, episode = [int(el) for el in episode[1:].split('e')]
    name = ' '.join(name)
    return name, {'episode' : episode, 
                  'season' : season
                 }

update(['http://api.myshows.ru/rss/1000324/episodes/aired/'],
       client, 'item', get_date, get_content)

print('updating youtube list')

def get_date(item): 
    return datetime.datetime.strptime(item.published.text[:10], 
                                               '%Y-%m-%d').date()

def get_content(item):
    name = item.author.find('name').text + ': ' + item.title.text
    link = item.link.get('href')
    return name, {'link'  : link}

def get_video(item):
    return item.link.get('href')

update(get_youtube_urls(), client, 'entry', get_date, get_content, get_video)

print('updating shows list')
def get_date(item):
    return datetime.datetime.strptime(item.text.split()[-1],
                                      '%d.%m.%Y').date()

def get_content(item):
    name = 'КВН: ' + item.text[:-27]
    link = 'https://www.1tv.ru/shows/kvn/vypuski'
    return name, {'link': link}
    
update(['https://www.1tv.ru/shows/kvn/vypuski'], 
       client, 'h3', get_date, get_content)    

def get_content(item):
    name = 'ЧГК: ' + item.text[:-39]
    link = 'https://www.1tv.ru/shows/chto-gde-kogda/vypuski'
    return name, {'link': link}

update(['https://www.1tv.ru/shows/chto-gde-kogda/vypuski'], 
       client, 'h3', get_date, get_content)

print('complete')
update_last_date(client)