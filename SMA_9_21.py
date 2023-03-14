# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

# --- Do not remove these libs ---
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


class SMA_9_21(IStrategy):
   
   
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy.
    timeframe = '4h'

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
       
        "0": 100
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.03

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
    buy_rsi = IntParameter(10, 40, default=30, space="buy")
    sell_rsi = IntParameter(60, 90, default=70, space="sell")

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
                "RSI": {
                    'rsi': {'color': 'red'},
                },
                "sma10": {
                    'sma10':{'color': 'blue'},
                },
                "sma21":{
                    'sma21':{'color': 'black'}
                }
            }
        }

    def informative_pairs(self):
       
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
       
        dataframe['sma10'] = ta.SMA(dataframe, timeperiod=9)
        dataframe['sma21'] = ta.SMA(dataframe, timeperiod=21)
      

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
       
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['sma10'], dataframe['sma21']))  
                
            ),
            'enter_long'] = 1

            #if sma9 crossed_above sma21 === enter_long
       
     

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
                            
        dataframe.loc[
            (
                (qtpylib.crossed_below(dataframe['sma10'], dataframe['sma21'])) 
                
            ),
            'exit_long'] = 1

            #if sma10 crossed_below sma21 === exit_long
      
        return dataframe
    

    """NOTES
    ta stret se je zdel great dokler ne pogruntaš the obvies thing da kjer se smaja križata ni price ampk je ponavad entry price dost višji, exit price pa dost višji,
    and thus the profit margin is razor thin...ta stret bi delvou če bi price perfekno sledil smaju, kar recimo je pr avalanchu, zato sm pa ujeu a 38% whopper of a trade.
    Ampk tud če bi usou 100% mojga accounta (50%) se nebi izlšlo, bi blo bolš sam hodlat"""