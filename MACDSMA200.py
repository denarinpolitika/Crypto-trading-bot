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
from functools import reduce

class MACDSMA200(IStrategy):

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
    stoploss = -0.50

    # Trailing stoploss
    trailing_stop = True
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

    buy_ema_short = IntParameter(7, 17, default=12)
    buy_ema_long = IntParameter(20, 35, default=26)
    sell_ema_short = IntParameter(7, 17, default=12)
    sell_ema_long = IntParameter(20, 35, default=26)
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
    
    # BINGO
    # U GOT SOMTHIN HERE, PF=3, 40 cagr... edini problem je 21 tradeov, probej še 12h timeframe pa probej kkšn secret sauce dodt
    # dodej dober trailing stop če gre da boš zavarovan pred bol volatile assets
    # Naj še par starih assetov na futuresih pa testirej
    # Probej manjši timeframe 12h, 6h
    # NE OVERFITTAT testirej zravn še druge assete, see how they respond
    # Ideja: nared zahtevnejše signale za shortanje mejbi??
    # Ko si zadovolen, runnej hyperopt

    # ko runnaš spodn command (z vsemi coini v config fijlu) z manj max open tradi se ti absolute profit abnormalno poveča, poveča se pa tud drawdown (20% pr 1 max open trades)
    # freqtrade backtesting --strategy MACDSMA200  --timeframe 1d --timerange 20190909-20221111

    # Mn ko daš max open tradou bol selective rata bot. dobesedno je "mn je več" situation ker bota missa bad opportunitys. Some times not making a trade is a trade in itself.
    # najbolši drawdown/profit ratio je na 5 in 3 s tem da je 3 way better sam se zdi unrealistic. Ampk lej bomo vidl.

    # prever če vse štima pa probej runnat hyperopt popoldne.
    # freqtrade hyperopt --hyperopt-loss SharpeHyperOptLoss --strategy MACDSMA200 -e 1000 --spaces buy, sell, stoploss

# HYPEROPT 1
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

# HYPEROPT 2

# Best result:

#    544/1000:    700 trades. 630/0/70 Wins/Draws/Losses. Avg profit   1.72%. Median profit   2.96%. Total profit 32285.70929172 USDT ( 645.71%). Avg duration 3 days, 14:12:00 min. Objective: -2.00641


#     # Buy hyperspace params:
#     buy_params = {
#         "buy_ema_long": 27,
#         "buy_ema_short": 17,
#     }

#     # Sell hyperspace params:
#     sell_params = {
#         "sell_ema_long": 27,
#         "sell_ema_short": 16,
#     }

#     # ROI table:  # value loaded from strategy
#     minimal_roi = {
#         "0": 100
#     }

#     # Stoploss:
#     stoploss = -0.335

#     # Trailing stop:
#     trailing_stop = True
#     trailing_stop_positive = 0.01
#     trailing_stop_positive_offset = 0.04
#     trailing_only_offset_is_reached = True

# +--------+-----------+----------+------------------+--------------+-------------------------------+-----------------+-------------+-------------------------------+
# |   Best |     Epoch |   Trades |    Win Draw Loss |   Avg profit |                        Profit |    Avg duration |   Objective |           Max Drawdown (Acct) |
# |--------+-----------+----------+------------------+--------------+-------------------------------+-----------------+-------------+-------------------------------|
# | * Best |    1/1000 |      485 |    201    0  284 |       -2.36% |     -4565.592 USDT  (-91.31%) | 4 days 09:48:00 |     1.82449 |      4792.136 USDT   (91.72%) |
# | * Best |    2/1000 |      190 |     55    0  135 |        2.39% |      3370.904 USDT   (67.42%) | 15 days 00:53:00 |    -0.29166 |      2790.699 USDT   (28.94%) |                                                                   
# | * Best |   13/1000 |      365 |    228    0  137 |        2.13% |     10131.603 USDT  (202.63%) | 7 days 02:14:00 |    -0.79011 |      6549.091 USDT   (30.56%) |                                                                    
# |   Best |  165/1000 |      720 |    350    0  370 |        0.86% |      8058.807 USDT  (161.18%) | 2 days 06:28:00 |    -0.99546 |      4781.598 USDT   (27.47%) |                                                                    
# |   Best |  174/1000 |      544 |    298    0  246 |        1.94% |     22831.854 USDT  (456.64%) | 3 days 15:21:00 |    -1.33788 |      8925.668 USDT   (24.90%) |                                                                    
# |   Best |  215/1000 |      679 |    519    0  160 |        1.60% |     25235.805 USDT  (504.72%) | 3 days 00:32:00 |    -1.63047 |      8358.032 USDT   (22.39%) |                                                                    
# |   Best |  228/1000 |      782 |    706    0   76 |        1.27% |     22364.960 USDT  (447.30%) | 2 days 20:34:00 |    -1.79387 |      7046.448 USDT   (42.27%) |                                                                    
# |   Best |  238/1000 |      769 |    703    0   66 |        1.43% |     26418.752 USDT  (528.38%) | 3 days 03:22:00 |    -1.94961 |      8330.588 USDT   (46.65%) |                                                                    
# |   Best |  433/1000 |      703 |    627    0   76 |        1.69% |     31011.307 USDT  (620.23%) | 3 days 11:49:00 |    -1.96411 |     11383.669 USDT   (51.95%) |                                                                    
# |   Best |  544/1000 |      700 |    630    0   70 |        1.72% |     32285.709 USDT  (645.71%) | 3 days 14:12:00 |    -2.00641 |     13707.832 USDT   (57.42%) |                                                                    
#  [Epoch 1000 of 1000 (100%)] ||                                                                                                                                                               | [Time:  0:58:07, Elapsed Time: 0:58:07]
# 2022-11-15 18:08:57,148 - freqtrade.optimize.hyperopt - INFO - 1000 epochs saved to '/workspaces/ft_userdata/user_data/hyperopt_results/strategy_MACDSMA200_2022-11-15_17-10-24.fthypt'.
# 2022-11-15 18:08:57,344 - freqtrade.optimize.hyperopt_tools - INFO - Dumping parameters to /workspaces/ft_userdata/user_data/strategies/MACDSMA200.json


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
    
  