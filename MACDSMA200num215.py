import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame  # noqa
from datetime import datetime  # noqa
from typing import Optional, Union  # noqa

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from functools import reduce

class MACDSMA200num215(IStrategy):

    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy.
    timeframe = '1d'

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {

        "0": 100
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.165

    # Trailing stoploss
    trailing_stop = True
    trailing_only_offset_is_reached = True
    trailing_stop_positive = 0.011
    trailing_stop_positive_offset = 0.047  # Disabled / not configured

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Strategy parameters

    buy_ema_short = IntParameter(7, 17, default=16)
    buy_ema_long = IntParameter(20, 35, default=25)
    sell_ema_short = IntParameter(7, 17, default=14)
    sell_ema_long = IntParameter(20, 35, default=35)


    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }
    
    @property
    def plot_config(self):
        return {
            # Main plot indicators (Moving averages, ...)
            'main_plot': {
                'tema': {},
                'sar': {'color': 'white'},
            },
            'subplots': {
                # Subplots - each dict defines one additional plot
                "MACD": {
                    'macd': {'color': 'blue'},
                    'macdsignal': {'color': 'orange'},
                },
               
            }
        }

    def informative_pairs(self):

        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        for val in self.buy_ema_short.range:
            dataframe[f'ema_short_{val}'] = ta.EMA(dataframe, timeperiod=val)

        # Calculate all ema_long values
        for val in self.buy_ema_long.range:
            dataframe[f'ema_long_{val}'] = ta.EMA(dataframe, timeperiod=val)
       

        for val in self.sell_ema_short.range:
            dataframe[f'ema_short_{val}'] = ta.EMA(dataframe, timeperiod=val)

        # Calculate all ema_long values
        for val in self.sell_ema_long.range:
            dataframe[f'ema_long_{val}'] = ta.EMA(dataframe, timeperiod=val)
        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']


                # # EMA - Exponential Moving Average
        # dataframe['ema3'] = ta.EMA(dataframe, timeperiod=3)
        # dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)
        # dataframe['ema12'] = ta.EMA(dataframe, timeperiod=12)
        # dataframe['ema26'] = ta.EMA(dataframe, timeperiod=26)
        # dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
        # dataframe['ema100'] = ta.EMA(dataframe, timeperiod=100)

        
        # # SMA - Simple Moving Average
        # dataframe['sma3'] = ta.SMA(dataframe, timeperiod=3)
        # dataframe['sma5'] = ta.SMA(dataframe, timeperiod=5)
        # dataframe['sma10'] = ta.SMA(dataframe, timeperiod=10)
        # dataframe['sma21'] = ta.SMA(dataframe, timeperiod=21)
        # dataframe['sma50'] = ta.SMA(dataframe, timeperiod=50)
        dataframe['sma200'] = ta.SMA(dataframe, timeperiod=200)

      

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []
        conditions.append(dataframe[f'ema_short_{self.buy_ema_short.value}'] > dataframe[f'ema_long_{self.buy_ema_long.value}'])
        conditions.append(dataframe['macdhist'] > 0)
        conditions.append(dataframe['macd'] > 0)
        conditions.append(dataframe['macdsignal'] > 0)
        conditions.append(dataframe['close'] > dataframe['sma200'])
        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'enter_long'] = 1
        '''
        dataframe.loc[
            (
                (dataframe['macdhist'] > 0) &
                (dataframe['macd'] > 0) &
                (dataframe['macdsignal'] > 0) &
                (dataframe['ema12'] > dataframe['ema26']) &
                (dataframe['close'] > dataframe['sma200']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1
        # Uncomment to use shorts (Only used in futures/margin mode. Check the documentation for more info)
        '''
        conditions = []
        conditions.append(dataframe[f'ema_short_{self.buy_ema_short.value}'] < dataframe[f'ema_long_{self.buy_ema_long.value}'])
        conditions.append(dataframe['macdhist'] < 0)
        conditions.append(dataframe['macd'] < 0)
        conditions.append(dataframe['macdsignal'] < 0)
        conditions.append(dataframe['close'] < dataframe['sma200'])
        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'enter_short'] = 1
        '''       
        dataframe.loc[
            (
                (dataframe['macdhist'] < 0) &
                (dataframe['macd'] < 0) &
                (dataframe['macdsignal'] < 0) &
                (dataframe['ema12'] < dataframe['ema26']) &
                (dataframe['close'] < dataframe['sma200']) &
                (dataframe['volume'] > 0)
            ),
            'enter_short'] = 1
        '''

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        
        conditions = []
        conditions.append(dataframe['macd'] < 0)
        conditions.append(qtpylib.crossed_below(dataframe[f'ema_short_{self.sell_ema_short.value}'], dataframe[f'ema_long_{self.sell_ema_long.value}']))
        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'exit_long'] = 1


        '''
        dataframe.loc[
            (
                (dataframe['macd'] < 0) &
                (qtpylib.crossed_below(dataframe['ema12'], dataframe['ema26'])) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
        '''
        # Uncomment to use shorts (Only used in futures/margin mode. Check the documentation for more info)
        conditions = []
        conditions.append(dataframe['macd'] > 0)
        conditions.append(qtpylib.crossed_above(dataframe[f'ema_short_{self.sell_ema_short.value}'], dataframe[f'ema_long_{self.sell_ema_long.value}']))
        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'exit_short'] = 1
        '''
        dataframe.loc[
            (
                (dataframe['macd'] > 0) &
                (qtpylib.crossed_above(dataframe['ema12'], dataframe['ema26'])) &
                (dataframe['volume'] > 0)
            ),
            'exit_short'] = 1
        '''
        return dataframe

        # HYPEROPT RESULT 215
# {"loss":-1.6304680821939683,
# "params_dict":{
#     "buy_ema_long":25
#     "buy_ema_short":16
#     "sell_ema_long":35
#     "sell_ema_short":14
#     "stoploss":-0.165
#     "trailing_stop":true
#     "trailing_stop_positive":0.011
#     "trailing_stop_positive_offset_p1":0.047
#     "trailing_only_offset_is_reached":true},
    
# hyperopt commmand
# freqtrade backtesting --strategy MACDSMA200num215  --timeframe 1d --timerange 20190909-20221111 --export trades