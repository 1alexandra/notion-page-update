from notion.block import VideoBlock

from notion_client import update_row


def is_equal(row, kwargs):
    return (row.title == kwargs['title']
            or row.link and kwargs['link']
            and row.link == kwargs['link'])


def old_episode(row, kwargs):
    return (row.season and kwargs['season']
            and int(row.season) > kwargs['season']
            or row.season == kwargs['season']
            and row.episode and kwargs['episode']
            and int(row.episode) > kwargs['episode'])


def update(cv, rows, rss, add_video=False):
    added_names = []
    for kwargs in rss:
        if kwargs['title'] in added_names:
            continue
        finded_row = None
        for row in rows:
            if is_equal(row, kwargs):
                finded_row = row
                break
        if finded_row is None:
            finded_row = cv.collection.add_row(title=kwargs['title'])
            added_names.append(kwargs['title'])
            if add_video:
                video = finded_row.children.add_new(VideoBlock)
                video.set_source_url(kwargs['link'])
        elif finded_row.date or old_episode(finded_row, kwargs):
            continue
        update_row(finded_row, kwargs)
