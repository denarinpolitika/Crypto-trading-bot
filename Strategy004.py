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


class Strategy004(IStrategy):
    """
    This is a strategy template to get you started.
    More information in https://www.freqtrade.io/en/latest/strategy-customization/

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_entry_trend, populate_exit_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    """
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "60":  0.01,
        "30":  0.03,
        "20":  0.04,
        "0":  0.05
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.10

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02  # Disabled / not configured

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = True
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Strategy parameters

    # Buy params

    # buy_rsi = IntParameter(10, 40, default=30, space="buy")
    # sell_rsi = IntParameter(60, 90, default=70, space="sell")
    buy_slowadx = IntParameter(15, 35, default=26, space="buy", optimize=True, load=True)
    buy_adx = IntParameter(40, 60, default=50, space="buy", optimize=True, load=True)
    buy_cci = IntParameter(-115, -85, default=-100, space="buy", optimize=True, load=True)
    buy_fastk_previous = IntParameter(10, 30, default=20, space="buy", optimize=True, load=True)
    buy_fastd_previous = IntParameter(10, 30, default=20, space="buy", optimize=True, load=True)
    buy_slowfastk_previous = IntParameter(20, 40 ,default=30, space="buy", optimize=True, load=True)
    buy_slowfastd_previous = IntParameter(20, 40 ,default=30, space="buy", optimize=True, load=True)
    buy_mean_volume = IntParameter(0.70, 0.80, default=0.75, space="buy", optimize=True, load=True)

    # Sell params

    sell_slowadx = IntParameter(15, 35, default=26, space="sell", optimize=True, load=True)
    sell_fastk = IntParameter(60, 80, default=70, space="sell", optimize=True, load=True)
    sell_fastd = IntParameter(60, 80, default=70, space="sell", optimize=True, load=True)

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
                }
            }
        }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame
        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        """

        # ADX
        dataframe['adx'] = ta.ADX(dataframe)
        dataframe['slowadx'] = ta.ADX(dataframe, 35)

        # Commodity Channel Index: values Oversold:<-100, Overbought:>100
        dataframe['cci'] = ta.CCI(dataframe)

        # Stoch
        stoch = ta.STOCHF(dataframe, 5)
        dataframe['fastd'] = stoch['fastd']
        dataframe['fastk'] = stoch['fastk']
        dataframe['fastk-previous'] = dataframe.fastk.shift(1)
        dataframe['fastd-previous'] = dataframe.fastd.shift(1)

        # Slow Stoch
        slowstoch = ta.STOCHF(dataframe, 50)
        dataframe['slowfastd'] = slowstoch['fastd'] # %D represents the 3-period average of %K.
        dataframe['slowfastk'] = slowstoch['fastk'] # %K represents the current price of the security, represented
        dataframe['slowfastk-previous'] = dataframe.slowfastk.shift(1) # as a percentage of the difference between its 
        dataframe['slowfastd-previous'] = dataframe.slowfastd.shift(1) # highest and lowest values over a certain time period.

        # EMA - Exponential Moving Average
        dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)

        dataframe['mean-volume'] = dataframe['volume'].mean()

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        dataframe.loc[
            (
                (
                    (dataframe['adx'] > self.buy_adx.value) |
                    (dataframe['slowadx'] > self.buy_slowadx.value) #če ma moderate to very strong trend
                ) &
                (dataframe['cci'] < self.buy_cci.value) & #če close crossa spodnjo mejo cci-ja
                (
                    (dataframe['fastk-previous'] < self.buy_fastk_previous.value) & # close more bit pod stoch, basicly oversold teritorij, pri K in D
                    (dataframe['fastd-previous'] < self.buy_fastd_previous.value)
                ) &
                (
                    (dataframe['slowfastk-previous'] < self.buy_fastk_previous.value) & #počasn prejšnji stoch (seprav pred sedanjim) more bit manjši od 30, pri K in D
                    (dataframe['slowfastd-previous'] < self.buy_fastd_previous.value)
                ) &
                (dataframe['fastk-previous'] < dataframe['fastd-previous']) & # K more bit manjši od D, sepravi more stoch odstopati od svojega 3 period povprečja 
                (dataframe['fastk'] > dataframe['fastd']) &
                (dataframe['mean-volume'] > self.buy_mean_volume.value) & 
                (dataframe['close'] > 0.00000100) # i guess crypto ne sme it v faking ground
            ),
            'enter_long'] = 1

        return dataframe
        # Uncomment to use shorts (Only used in futures/margin mode. Check the documentation for more info)
        """
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['rsi'], self.sell_rsi.value)) &  # Signal: RSI crosses above sell_rsi
                (dataframe['tema'] > dataframe['bb_middleband']) &  # Guard: tema above BB middle
                (dataframe['tema'] < dataframe['tema'].shift(1)) &  # Guard: tema is falling
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'enter_short'] = 1
        """

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with exit columns populated
        """
        dataframe.loc[
            (
                (dataframe['slowadx'] < self.sell_slowadx.value) &
                ((dataframe['fastk'] > self.sell_fastk.value) | (dataframe['fastd'] > self.sell_fastd.value)) &
                (dataframe['fastk-previous'] < dataframe['fastd-previous']) &
                (dataframe['close'] > dataframe['ema5'])
            ),
            'exit_long'] = 1
        return dataframe
        # Uncomment to use shorts (Only used in futures/margin mode. Check the documentation for more info)
        """
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['rsi'], self.buy_rsi.value)) &  # Signal: RSI crosses above buy_rsi
                (dataframe['tema'] <= dataframe['bb_middleband']) &  # Guard: tema below BB middle
                (dataframe['tema'] > dataframe['tema'].shift(1)) &  # Guard: tema is raising
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'exit_short'] = 1
        """
        return dataframe
    