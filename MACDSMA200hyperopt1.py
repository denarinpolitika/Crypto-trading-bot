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

class MACDSMA200hyperopt1(IStrategy):

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
    stoploss = -0.02

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Strategy parameters

    buy_ema_short = IntParameter(7, 17, default=11)
    buy_ema_long = IntParameter(20, 35, default=24)

    # Optional order type mapping.
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
        conditions.append(qtpylib.crossed_below(dataframe[f'ema_short_{self.buy_ema_short.value}'], dataframe[f'ema_long_{self.buy_ema_long.value}']))
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
        conditions.append(qtpylib.crossed_above(dataframe[f'ema_short_{self.buy_ema_short.value}'], dataframe[f'ema_long_{self.buy_ema_long.value}']))
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

        # Best result:

#    315/1000:    366 trades. 25/0/341 Wins/Draws/Losses. Avg profit   3.71%. Median profit  -2.04%. Total profit 9419.82067092 USDT ( 188.40%). Avg duration 9 days, 4:47:00 min. Objective: -0.64235


#     # Buy hyperspace params:
#     buy_params = {
#         "buy_ema_long": 24,
#         "buy_ema_short": 11,
#     }

#     # ROI table:  # value loaded from strategy
#     minimal_roi = {
#         "0": 100
#     }

#     # Stoploss:
#     stoploss = -0.02

#     # Trailing stop:
#     trailing_stop = False  # value loaded from strategy
#     trailing_stop_positive = None  # value loaded from strategy
#     trailing_stop_positive_offset = 0.0  # value loaded from strategy
#     trailing_only_offset_is_reached = False  # value loaded from strategy
    