import urllib
import calendar
import datetime
import requests
import lxml.html
import pandas as pd
from collections import OrderedDict
from typing import Tuple


def _getResponseYFHist(code: str, dt_start: datetime.datetime, dt_end: datetime.datetime) -> requests.models.Response:
    ts1 = dt_start.timestamp()  # 조회 시작 시점, UNIX 타임스탬프로 변경
    ts2 = dt_end.timestamp()  # 조회 종료 시점, UNIX 타임스탬프로 변경

    url = "https://finance.yahoo.com/quote/"
    url += urllib.parse.quote(code) + "/history"  # 종목코드 퍼센트 인코딩
    params = {
        "period1": int(ts1),
        "period2": int(ts2),
        "interval": "1d",
        "filter": "history",
        "frequency": "1d",
        "includeAdjustedClose": "true"
    }
    headers = {
        "USER-AGENT": "Mozilla/5.0"
    }

    return requests.get(url, params=params, headers=headers)


def _getResponseYFHistDataMonthly(code: str, year: int, month: int) -> requests.models.Response:
    target_month = datetime.datetime(year, month, 1, 9)  # 오전 9시
    dt_start = target_month - datetime.timedelta(weeks=1)  # 지난달의 마지막 종가를 알아야 변동률 계산 가능
    days_in_month = calendar.monthrange(year, month)[1]  # 해당 월의 총 일 수 자동 계산
    dt_end = target_month + datetime.timedelta(days=days_in_month) - datetime.timedelta(hours=9)
    return _getResponseYFHist(code, dt_start, dt_end)


def _getResponseYFHistDataYearly(code: str, year: int) -> requests.models.Response:
    dt_start = datetime.datetime(year, 1, 1, 9)
    dt_end = datetime.datetime(year + 1, 1, 1, 9)
    return _getResponseYFHist(code, dt_start, dt_end)


def _createDataFrameFromResponse(response: requests.models.Response):
    tree = lxml.html.fromstring(response.text)
    table = tree.find_class("W(100%) M(0)")[0]  # history 테이블 요소 찾기

    # 테이블 칼럼명 가져오기
    column_names = []
    thead = table.find("thead")
    tr = thead.find("tr")
    th = tr.findall("th")
    for head in th:
        span = head.find("span")
        column_names.append(span.text)
    column_names = [x.replace('*', '') for x in column_names]  # 특수문자(*) 지워주기

    # 테이블 모든 행 정보 가져오기
    tbody = table.find("tbody")
    tr = tbody.findall("tr")
    data_list = list()
    for row in tr:
        valid = True
        data = OrderedDict()
        td = row.findall("td")
        for idx, elem in enumerate(td):
            span = elem.find("span")
            if span is not None:
                data[column_names[idx]] = span.text.replace(',', '')  # 쉼표 제거
            else:
                # data[column_names[idx]] = 0
                # TODO: warning message
                valid = False
                break
        if valid:
            data_list.append(data)

    # 데이터프레임 생성
    df = pd.DataFrame(data_list)

    # 자료형 변경
    df["Date"] = pd.to_datetime(df["Date"], format="%b %d %Y")
    df["Open"] = df["Open"].astype(float)
    df["High"] = df["High"].astype(float)
    df["Low"] = df["Low"].astype(float)
    df["Close"] = df["Close"].astype(float)
    df["Adj Close"] = df["Adj Close"].astype(float)
    df["Volume"] = df["Volume"].astype(float)

    # 날짜 오름차순으로 정렬
    df.sort_values(by="Date", ascending=True, inplace=True, ignore_index=True)
    return df


def getYFHistData(code: str, dt_start: datetime.datetime, dt_end: datetime.datetime, last_close_val: bool = False):
    if last_close_val:
        day_start = datetime.datetime(dt_start.year, dt_start.month, 1)
        response = _getResponseYFHist(code, day_start, dt_end)
    else:
        response = _getResponseYFHist(code, dt_start, dt_end)
    print(f'Query URL: {response.url}')
    result_df = _createDataFrameFromResponse(response)
    if last_close_val:
        # find record matches start datetime
        name = result_df.columns[0]
        index = result_df[result_df[name] == dt_start].index[0]
        last_month_close_value = result_df.iloc[index - 1]["Close"]
        return result_df.iloc[index:], last_month_close_value
    return result_df


def getYFHistDataMonthly(code: str, year: int, month: int) -> Tuple[pd.DataFrame, float]:
    response = _getResponseYFHistDataMonthly(code, year, month)
    print(f'Query URL: {response.url}')
    result_df = _createDataFrameFromResponse(response)
    # 해당 month에 해당하는 데이터프레임만 따로 추출
    month_series = pd.to_datetime(result_df["Date"]).dt.month
    # 지난달의 마지막 날의 종가는 따로 반환
    last_month_close_value = result_df[month_series != month].iloc[-1]["Close"]

    return result_df[month_series == month], last_month_close_value
