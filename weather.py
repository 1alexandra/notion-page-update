import os
from datetime import datetime, timezone, timedelta
import requests
import yaml

from notion_client import update_row
from update import is_equal


def weather_api_url(geo):
    url = 'https://api.weather.yandex.ru/v2'
    return f'{url}/informers?lat={geo[0]}&lon={geo[1]}'


def yandex_weather(geo, key):
    try:
        headers = {'X-Yandex-API-Key': key}
        res = requests.get(weather_api_url(geo),
                           headers=headers)
        return res.json()
    except Exception:
        return {}


def read_from_yaml(
    yaml_path='need_weather.yaml',
    ret_time_parts=False,
    ret_need_weather=False
):
    with open('need_weather.yaml', 'r') as f:
        dump = yaml.safe_load(f)
    time_parts = dump['time_parts']
    need_weather = dump['need_weather']
    if ret_time_parts and ret_need_weather:
        return time_parts, need_weather
    if ret_time_parts:
        return time_parts
    if ret_need_weather:
        return need_weather
    return None


def time_part_name(from_utc_hours=3):
    utc = datetime.now(timezone.utc)
    now = utc + timedelta(hours=from_utc_hours)
    hour = now.hour
    time_parts = read_from_yaml(ret_time_parts=True)
    for part_name, hours in time_parts.items():
        if hour in hours:
            return part_name, now.weekday(), str(now.date())
    return None


def next_time_part_names(from_utc_hours=3):
    return time_part_name(from_utc_hours+6), time_part_name(from_utc_hours+12)


def get_weather_title(forecast_date, geo_name, part_name):
    return f'{forecast_date}, {geo_name}, {part_name}'


def need_forecast(rows, geo, from_utc_hours=3):
    need_weather = read_from_yaml(ret_need_weather=True)
    for (part, weekday, date) in next_time_part_names(from_utc_hours):
        if weekday not in need_weather[geo][part]:
            continue
        title = get_weather_title(date, geo, part)
        finded = False
        for row in rows:
            if row.title == title:
                finded = True
                break
        if not finded:
            return True
    return False


def add_forecast(cv, rows, geo_name, geo, yandex_api_key):
    res = yandex_weather(geo, yandex_api_key)
    forecast = res['forecast']
    forecast_url = res['info']['url']
    forecast_date = forecast['date']
    for part in forecast['parts']:
        kwargs = part.copy()
        icon_path = f'https://yastatic.net/weather/i/icons/blueye/color/svg/'
        kwargs.update({
            'title': get_weather_title(
                forecast_date, geo_name, part['part_name']
            ),
            'geo': geo_name,
            'date': datetime.strptime(forecast_date, "%Y-%m-%d").date(),
            'url': forecast_url,
            'icon': icon_path + f'{kwargs["icon"]}.svg',
        })
        finded_row = None
        for row in rows:
            if is_equal(row, kwargs):
                finded_row = row
                break
        if finded_row is not None:
            continue
        row = cv.collection.add_row(title=kwargs['title'])
        update_row(row, kwargs)


def build_geos(names=['home', 'work']):
    return {
        name:
        (float(os.environ[f'geo_{name}_latitude']),
         float(os.environ[f'geo_{name}_longitude']))
        for name in names
    }


def get_key(i=0):
    return os.environ[f'yandex_key_{i}']


def update_weather(cv, rows, key_num=3):
    for geo_name, geo in build_geos().items():
        if need_forecast(rows, geo_name):
            for i in range(key_num):
                try:
                    add_forecast(cv, rows, geo_name, geo, get_key(i))
                    break
                except Exception:
                    continue
    for row in rows:
        if row.date.start < datetime.now().date():
            row.remove()
