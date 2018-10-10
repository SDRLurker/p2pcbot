# -*- coding: utf-8 -*-
import json
import asyncio
import requests
import collections

URL_TEMPL = "https://api.bithumb.com/public/ticker/%s"
URL_ALL = "https://api.bithumb.com/public/ticker/ALL"


class Bithumb:
    def __init__(self, currency=""):
        self.url = URL_TEMPL % currency

    def set_currency(self, currency):
        self.url = URL_TEMPL % currency

    def get_ohlcs(self, data):
        quote = collections.OrderedDict()
        try:
            quote['open'] = float(data['opening_price'])
            quote['high'] = float(data['max_price'])
            quote['low'] = float(data['min_price'])
            quote['close'] = float(data['closing_price'])
            quote['change'] = quote['close'] - quote['open']
            quote['rate'] = quote['change'] / quote['open'] * 100.0
        except Exception as e:
            print("get_ohlcs error", str(e))
            quote = collections.OrderedDict()
        return quote

    def get_quote(self):
        quote = {}
        res = requests.get(self.url)
        quote_json = json.loads(res.text)
        if 'status' in quote_json and quote_json['status'] == '0000':
            quote = self.get_ohlcs(quote_json['data'])
        return quote

    def get_all_quote(self):
        quote = {}
        # https://stackoverflow.com/questions/23013220/max-retries-exceeded-with-url
        try:
            res = requests.get(URL_ALL)
            quote_json = json.loads(res.text)
        except Exception as e:
            print("get_all_quote error", str(e))
            return quote
        if 'status' in quote_json and quote_json['status'] == '0000':
            for currency in quote_json['data']:
                if currency == 'date':
                    continue
                quote[currency] = self.get_ohlcs(quote_json['data'][currency])
        return quote


class AsyncBithumb(Bithumb):
    def __init__(self, wait_sec, currency=""):
        self.wait_sec = wait_sec
        self.url = URL_TEMPL % currency

    async def __aenter__(self):
        await asyncio.sleep(self.wait_sec)
        return self.get_all_quote()

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass


async def main():
    while True:
        async with AsyncBithumb(1) as result:    # async with에 클래스의 인스턴스 지정
            print(result)    # 3

if __name__ == "__main__":
    exch = Bithumb()
    exch.set_currency('BTG')
    print(exch.get_quote())
    print(exch.get_all_quote())

    print()
    print("====ASYNC====")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
