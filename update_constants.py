import yaml

urls = {
    'WHAT_TO_WATCH': "https://www.notion.so/zhuav/0a23057cdbc141d8b20667573857d8be?v=9154c0f034bf45c3b1269e9d8a3cd0b2",
    'YOUTUBE_LIST': "https://www.notion.so/zhuav/3745c12264d7475f8cad58c789cfaf72?v=74df3a81051a4a19aca2de91d381ee71",
    'MANGA_RSS': "https://grouple.co/user/rss/1667979",
    'SERIES_ON_RSS': "http://api.myshows.ru/rss/1000324/episodes/aired/",
    'LOGS_TABLE': "https://www.notion.so/zhuav/1c66987cc41f4c538b4cc207b029d625?v=81c4e36d8c0f43c6a6d81ca90a9609c5",
}

to_dump = {'URLS': urls}

with open('constants.yaml', 'w') as f:
    yaml.dump(to_dump, f)