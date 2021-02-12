import os
import pandas as pd
import numpy as np

import chart_studio.plotly as py
from chart_studio.tools import set_config_file
import plotly.graph_objects as go

from work_hours import week_start


def plotly_setup():
    user = os.environ['plotly_user']
    key = os.environ['plotly_key']
    py.sign_in(username=user, api_key=key)
    set_config_file(
        plotly_domain="https://plotly.com",
        plotly_api_domain="https://api.plotly.com"
    )


def work_hours_daily(wh_rows):
    timing = []
    for row in wh_rows:
        h = row.hours or 0
        m = row.minutes or 0
        time = (h * 60 + m) / 60
        timing.append([row.date.start, round(time, 2)])
    timing = pd.DataFrame(timing, columns=['Date', 'Hours'])
    all_dates = pd.date_range(timing.Date.min(), timing.Date.max(), freq='D')
    all_dates = pd.DataFrame(all_dates, columns=['Date'])
    return all_dates.merge(timing, 'left')


def work_hours_weekly(daily):
    daily['Week'] = daily.Date.apply(week_start)
    return daily.groupby('Week')['Hours'].mean().replace(0, np.nan)


def plot_work_hours(rows):
    daily = work_hours_daily(rows)
    weekly = work_hours_weekly(daily)
    data = [
        go.Scatter(
            x=daily.Date,
            y=daily.Hours,
            mode='markers',
            name='Days',
        ),
        go.Scatter(
            x=weekly.index,
            y=weekly.values,
            mode='lines+markers',
            name='Weeks',
        ),
    ]
    plotly_setup()
    py.plot(data, filename='example', sharing='public')
