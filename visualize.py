import datetime

import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mpl_dates
from functions import *


indices = [
    {"name": "S&P 500", "code": "^GSPC"},
    {"name": "NASDAQ", "code": "^IXIC"},
    {"name": "Dow", "code": "^DJI"},
    {"name": "KOSPI", "code": "^KS11"},
    {"name": "KOSDAQ", "code": "^KQ11"},
    {"name": "NIKKEI 225", "code": "^N225"},
    {"name": "HANGSENG", "code": "^HSI"},
    {"name": "SHANGHAI", "code": "000001.SS"}
]

for elem in indices:
    # elem["data"] = getYFHistDataMonthly(elem["code"], 2022, 7)
    # df, last_close_val = getYFHistDataMonthly(elem["code"], 2022, 12)
    df, last_close_val = getYFHistData(elem["code"], datetime.datetime(2022,11,30), datetime.datetime(2022,12,30), last_close_val = True)
    elem["data"] = df
    elem["last_close_val"] = last_close_val

fig, ax = plt.subplots(nrows=4, ncols=2, figsize=(12, 12))
date_format = mpl_dates.DateFormatter("%Y.%m.%d")

for i, elem in enumerate(indices):
    data = elem["data"][["Date", "Open", "High", "Low", "Close"]].copy()

    ####################################################################################################################
    """
    if data.iloc[0]['Date'].day == 1:
        data = data.iloc[1:]
    """
    ####################################################################################################################
    # value1 = data.iloc[0]['Close']
    value1 = elem.get('last_close_val')
    data = data.iloc[1:]
    value2 = data.iloc[-1]['Close']
    cal = (value2 - value1) / value1 * 100
    print(f"{elem['name']}, {elem['code']}, {value1}, {value2}, {cal}")

    data["Date"] = pd.to_datetime(data["Date"])
    data["Date"] = data["Date"].apply(mpl_dates.date2num)

    candlestick_ohlc(ax[i // 2][i % 2], data.values, width=0.6, colorup="red", colordown="blue", alpha=0.8)
    ax[i // 2][i % 2].xaxis.set_major_formatter(date_format)
    
    title = "{}\n{:g}%".format(elem["name"], cal)
    ax[i // 2][i % 2].set_title(title)
fig.autofmt_xdate()
fig.tight_layout()
plt.tight_layout()
plt.savefig('result.png', dpi=200)
plt.show()
