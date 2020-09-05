import os

from datetime import datetime, timedelta
from notion.client import NotionClient


def find_file(filename):
    dir_path = os.getcwd()
    parent_dir_path = dir_path[:dir_path.rfind(os.sep)]
    for folder in [dir_path, parent_dir_path]:
        for root, dirs, files in os.walk(parent_dir_path):
            for file in files:
                if file == filename:
                    return root + os.sep + file
    raise Exception('find_file error')


def get_client():
    if 'TOKEN_V2' in os.environ:
        token = os.environ['TOKEN_V2']
    else:
        token_path = find_file('token.txt')
        if token_path is not None:
            with open(token_path, 'r') as file:
                token = file.read()
        else:
            return None
    try:
        return NotionClient(token_v2=token)
    except Exception:
        raise Exception('Error: wrong token_v2')


def get_cv_rows(client, url):
    cv = client.get_collection_view(url)
    rows = cv.default_query().execute()
    return cv, rows


def update_row(row, kwargs):
    for key, val in kwargs.items():
        if val:
            try:
                row.set_property(key, val)
            except Exception:
                pass


def get_last_date(rows):
    for row in rows:
        if row.title == 'last_date.txt':
            return row.date.start
    raise Exception('get_last_date error')


def update_last_date(rows):
    today = datetime.now().date()
    old = today - timedelta(days=1)
    updated = False
    for row in rows:
        if row.title == 'last_date.txt':
            row.date = today
            updated = True
        elif row.date is not None and row.seen:
            if row.episode is not None:
                row.episode = int(row.episode) + 1
                row.seen = False
                row.date = None
            elif row.date.start <= old:
                row.remove()
    if not updated:
        raise Exception('update_last_date error')
