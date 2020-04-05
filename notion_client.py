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
    return None


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
    return NotionClient(token_v2=token)


def update_row(row, kwargs):
    for key, val in kwargs.items():
        if val:
            row.set_property(key, val)


def get_last_date(rows):
    for row in rows:
        if row.title == 'last_date.txt':
            return row.date.start
    return None


def update_last_date(rows):
    today = datetime.now().date()
    old = today - timedelta(days=1)
    for row in rows:
        if row.title == 'last_date.txt':
            row.date = today
        elif (row.date is not None and row.date.start <= old
              and row.seen == 'yes'):
            row.remove()
