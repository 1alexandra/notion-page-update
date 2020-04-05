from soup import get_soup
from notion_client import update_row


def get_youtube_info(url):
    if 'channel' in url:
        tag = 'channel'
    elif 'playlist' in url:
        tag = 'playlist'
    elif 'user' in url:
        tag = 'user'
    else:
        return {}
    sep = '=' if tag == 'playlist' else '/'
    id_ = url.split(sep)[-1]
    prefix = 'https://www.youtube.com/feeds/videos.xml?'
    postfix = '_id=' if tag != 'user' else '='
    xml = prefix + tag + postfix + id_
    soup = get_soup(xml)
    name = soup.find('title').text
    return {
        'name': name,
        'tag': tag,
        'rss': xml
    }


def get_youtube_urls(rows):
    urls = []
    for row in rows:
        if not row.rss:
            update_row(row, get_youtube_info(row.link))
        urls.append(row.rss)
    return urls
