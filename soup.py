from bs4 import BeautifulSoup
import requests


def get_soup(url):
    try:
        session_requests = requests.session()
        result = session_requests.get(url, headers=dict(referer=url))
        return BeautifulSoup(result.content, features="lxml")
    except Exception:
        raise Exception('get_soup error')
