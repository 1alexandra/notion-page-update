from datetime import datetime, timedelta


def get_next_able(able_list, prev):
    for i, able in enumerate(able_list):
        if str(able) == str(prev):
            return able_list[(i + 1) % len(able_list)]
    return able_list[0]


def get_indicator(delta, days):
    cur_dates = delta.days
    indicator_list = ['clean', 'early', 'soon', 'time', 'late', 'dirty']
    steps = [- 2 * days / 3, - days / 3, 0, days / 3, 2 * days / 3]
    for i, step in enumerate(steps):
        if cur_dates < steps[i]:
            return indicator_list[i]
    return indicator_list[-1]


def fill_tody_next(row):
    days = row.weeks * 7
    row.who = get_next_able(row.able, row.prev)
    row.when = row.last.start + timedelta(days=days)


def update_tody(rows):
    for row in rows:
        date = datetime.today().date()
        days = row.weeks * 7
        fill_tody_next(row)
        if row.done:
            row.prev = row.who
            row.last = date
            fill_tody_next(row)
            row.done = False
        row.indicator = get_indicator(date - row.when.start, days)


def update_private(rows):
    for row in rows:
        date = datetime.today().date()
        days = row.days
        if row.done:
            row.last = date
            row.done = False
        row.when = row.last.start + timedelta(days=days)
        row.indicator = get_indicator(date - row.when.start, days)
