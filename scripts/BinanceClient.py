import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import requests


class BinanceClient:
    def __init__(self, futures, api_key=None, api_secret=None):
        self.base_url = None
        self.future = None

        self.api_key = api_key
        self.api_secret = api_secret

        self.set_futures(futures)

        server_time = self.get_server_time()
        client_time = int(time.time() * 1000)
        self.time_diff = server_time - client_time

    def set_futures(self, futures):
        self.future = futures
        self.base_url = 'https://testnet.binancefuture.com' if futures else 'https://testnet.binance.vision'

    def req(self, path, method='GET', data=dict(), headers=dict(), auth=False, sign=False):
        url = f'{self.base_url}{path}'

        if not auth and sign:
            raise Exception('Authorization is required to perform signature request')

        if auth and not self.api_key:
            raise Exception('API Key is required for authorization request')

        if sign and not self.api_secret:
            raise Exception('API secret is required for signature request')

        if method.upper() == 'POST':
            headers['Content-Type'] = 'application/json'

        if auth is True:
            headers['X-MBX-APIKEY'] = self.api_key

        # remove fields with missing values
        data = {key: val for key, val in data.items() if val is not None}

        if sign is True:
            data['timestamp'] = int(self.current_time())
            query_string = urlencode(data)

            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            data['signature'] = signature

        res = requests.request(method, url, headers=headers, params=data)

        if not res.ok:
            raise Exception(f'{res.status_code} - {res.url} - {res.content}')

        return json.loads(res.content)

    def current_time(self):
        client_time = int(time.time() * 1000)
        return client_time + self.time_diff

    def get_server_time(self):
        data = self.req('/fapi/v1/time' if self.future else '/api/v1/time')
        return data['serverTime']

    def test(self):
        self.req('/fapi/v1/ping' if self.future else '/api/v1/ping')
        print("Connection successful")

    def get_symbols(self):
        data = self.req('/fapi/v1/exchangeInfo' if self.future else '/api/v1/exchangeInfo')
        return data['symbols']

    def filter_symbols(self, min_years=None, **kwargs):
        def func(symbol):
            for key in kwargs:
                if min_years is not None:
                    time_diff = (time.time() * 1000) - symbol['onboardDate']
                    year_data = time_diff / (365.25 * 24 * 3600 * 1000)
                    if year_data < min_years:
                        return False

                return symbol[key].upper() == kwargs[key].upper()

        return func

    def get_historical_data(self, symbol: str, interval: str = '1m', start_time=None, end_time=None,
                            contract_type=None):
        """
        This function returns the Open time, open, high, low, close, volume for a given symbol

        Parameter:
        ----------
            symbol(str): The symobol we want the data
            interval(str): the interval of the data:
                ENUM: s-> seconds; m -> minutes; h -> hours; d -> days; w -> weeks; M -> months
                        - 1s
                        - 1m, 3m, 5m, 15m, 30m
                        - 1h, 2h, 4h, 6h, 8h, 12h
                        - 1d, 3d, 1w
                        - 1M
            startTime (Optional[int]): The starting timestamp (Unix time) for the data retrieval.
            endTime (Optional[int]): The ending timestamp (Unix time) for the data retrieval.

        Returns: ------- candlestick(List): Contains Open time, open, high, low, close prices and volume data for the
        given symbol and interval.
        """

        params = dict()

        params['symbol'] = symbol
        params['interval'] = interval
        params['limit'] = 1500

        if start_time is not None:
            params['startTime'] = start_time
        if end_time is not None:
            params['endTime'] = end_time
        if contract_type is not None:
            params['contractType'] = contract_type

        data = self.req('/fapi/v1/klines' if self.future else '/api/v1/klines', data=params)
        candles = []

        # to fetch the timestamp, open, high, low, close, volume
        if data is not None:
            for candle in data:
                candles.append((
                    float(candle[0]), float(candle[1]), float(candle[2]), float(candle[3]), float(candle[4]),
                    float(candle[5])))
            return candles

        else:
            return None

    def create_order(self, symbol, side, order_type,
                     position_side=None,
                     time_in_force=None,
                     quantity=None,
                     reduce_only=None,
                     price=None,
                     new_client_order_id=None,
                     stop_price=None,
                     close_position=None,
                     activation_price=None,
                     callback_rate=None,
                     working_type=None,
                     price_protect=None,
                     new_order_resp_type=None,
                     price_match=None,
                     self_trade_prevention_mode=None,
                     recv_window=None):
        """
        Implements the creation of an order,
        for details see https://binance-docs.github.io/apidocs/futures/en/#new-order-trade or
        https://binance-docs.github.io/apidocs/testnet/en/#new-order-trade
        """

        param = dict()

        order_type = order_type.upper()

        if order_type == "LIMIT":
            if time_in_force is None:
                raise Exception('For a LIMIT order "timeInForce" is required')
            if quantity is None:
                raise Exception('For a LIMIT order "quantity" is required')
            if price is None:
                raise Exception('For a LIMIT order "price" is required')
        elif order_type == "MARKET":
            if quantity is None:
                raise Exception('For a MARKET order "quantity" is required')
        elif order_type == "STOP" or order_type == "TAKE_PROFIT":
            if quantity is None:
                raise Exception('For a STOP/TAKE_PROFIT	order "quantity" is required')
            if price is None:
                raise Exception('For a STOP/TAKE_PROFIT	order "price" is required')
            if stop_price is None:
                raise Exception('For a STOP/TAKE_PROFIT	order "stopPrice" is required')
        elif order_type == "STOP_MARKET" or order_type == "TAKE_PROFIT_MARKET":
            if stop_price is None:
                raise Exception('For a STOP_MARKET/TAKE_PROFIT_MARKET order "stopPrice" is required"')
        elif order_type == "TRAILING_STOP_MARKET":
            if quantity is None:
                raise Exception('For a TRAILING_STOP_MARKET	order "quantity" is required')
            if callback_rate is None:
                raise Exception('For a TRAILING_STOP_MARKET	order "callbackRate" is required')

        param['symbol'] = symbol
        param['side'] = side
        param['type'] = order_type
        param['positionSide'] = position_side
        param['timeInForce'] = time_in_force
        param['quantity'] = quantity
        param['reduceOnly'] = reduce_only
        param['price'] = price
        param['newClientOrderId'] = new_client_order_id
        param['stopPrice'] = stop_price
        param['closePosition'] = close_position
        param['activationPrice'] = activation_price
        param['callbackRate'] = callback_rate
        param['workingType'] = working_type
        param['priceProtect'] = price_protect
        param['newOrderRespType'] = new_order_resp_type
        param['priceMatch'] = price_match
        param['selfTradePreventionMode'] = self_trade_prevention_mode
        param['recvWindow'] = recv_window

        data = self.req('/fapi/v1/order' if self.future else '/fapi/v1/order', method='POST', data=param, auth=True,
                        sign=True)

        return data
