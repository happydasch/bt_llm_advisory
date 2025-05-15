import os
from datetime import datetime, timedelta, UTC

from dotenv import load_dotenv, dotenv_values
import backtrader as bt
from tl_bt_adapter import (
    TLBackBroker,
    TLLiveBroker,
    TLData,
)

from bt_llm_advisory import BacktraderLLMAdvisory
from bt_llm_advisory.advisors import (
    BacktraderStrategyAdvisor,
    BacktraderPersonaAdvisor,
    BacktraderFeedbackAdvisor,
    BacktraderCandlePatternAdvisor,
    BacktraderTechnicalAnalysisAdvisor,
    BacktraderTrendAdvisor,
)

load_dotenv()

bot_advisory = BacktraderLLMAdvisory(
    model_provider_name=os.getenv("LLM_MODEL_PROVIDER"),
    model_name=os.getenv("LLM_MODEL"),
    model_config={"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")},
    advisors=[
        BacktraderTrendAdvisor(
            long_ma_period=25,
            short_ma_period=10,
            lookback_period=10,
            add_all_data_feeds=True,
        ),
        # BacktraderCandlePatternAdvisor(lookback_period=10, add_all_data_feeds=True),
        BacktraderStrategyAdvisor(),
        BacktraderTechnicalAnalysisAdvisor(),
        BacktraderFeedbackAdvisor(),
        # BacktraderPersonaAdvisor("Technical advisor", "intraday trader"),
        # BacktraderPersonaAdvisor(
        #     "Warren Buffett",
        #     (
        #         "A long-term fundamental investor who avoids market noise and focuses on intrinsic value.\n"
        #         "Preferred Investment Types: stocks, private equity\n"
        #         "Preferred Timeframes: monthly to yearly\n"
        #         "Special Knowledge: business valuation, economic moats, compound interest\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Paul Tudor Jones",
        #     (
        #         "A tactical trader with an edge in reading market psychology and momentum.\n"
        #         "Preferred Investment Types: forex, commodities, equities\n"
        #         "Preferred Timeframes: 4H to daily\n"
        #         "Special Knowledge: macro fundamentals, technical divergence, volatility spikes\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Stanley Druckenmiller",
        #     (
        #         "An adaptive macro investor with a strong sense for capital flow shifts.\n"
        #         "Preferred Investment Types: forex, equities, crypto\n"
        #         "Preferred Timeframes: swing (daily-weekly)\n"
        #         "Special Knowledge: macro narrative interpretation, position sizing, liquidity cycles\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Jesse Livermore",
        #     (
        #         "A classic trend follower and breakout trader.\n"
        #         "Preferred Investment Types: stocks, commodities\n"
        #         "Preferred Timeframes: daily to weekly\n"
        #         "Special Knowledge: price action, market timing, pyramiding\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Linda Raschke",
        #     (
        #         "A short-term technical trader who thrives in fast-moving markets.\n"
        #         "Preferred Investment Types: futures, forex\n"
        #         "Preferred Timeframes: 15-min to 4H\n"
        #         "Special Knowledge: market structure, oscillator timing, mean-reversion setups\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Peter Brandt",
        #     (
        #         "A disciplined classical chartist focusing on well-defined pattern setups.\n"
        #         "Preferred Investment Types: commodities, crypto, forex\n"
        #         "Preferred Timeframes: daily to weekly\n"
        #         "Special Knowledge: chart patterns, breakout confirmation, risk management\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Michael Burry",
        #     (
        #         "A contrarian value investor with a specialty in crisis detection.\n"
        #         "Preferred Investment Types: equities, CDS, macro derivatives\n"
        #         "Preferred Timeframes: multi-week to multi-year\n"
        #         "Special Knowledge: forensic analysis, systemic risk detection\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Richard Dennis",
        #     (
        #         "A trend-following system trader using strict entry/exit rules.\n"
        #         "Preferred Investment Types: futures, commodities, forex\n"
        #         "Preferred Timeframes: daily\n"
        #         "Special Knowledge: Turtle Trading rules, volatility-based risk control, position scaling\n"
        #     ),
        # ),
    ],
    max_concurrency=3,
)


class TestStrategy(bt.Strategy):

    def __init__(self):
        bot_advisory.init_strategy(self)
        self.ma = bt.indicators.SMA(period=10)
        self.ma2 = bt.indicators.SMA(period=40)

    def stop(self):
        print("STOP")

    def prenext(self):
        print("PRENEXT", self.data0.datetime.datetime(0), len(self.data0))

    def next(self):
        if self.data0.isdelayed():
            print("DELAYED DATA", len(self.data0))
            return
        print("NEXT", self.data0.datetime.datetime(0), len(self.data0))

        advisory_response = bot_advisory.get_advisory()

        print("\n", "ADDITIONAL DATA", "-" * 80, "\n")
        print(advisory_response.state.data)

        print("\n", "MESSAGES", "-" * 80, "\n")
        for message in advisory_response.state.messages:
            print(f"{message.__class__.__name__} {message.name}: {message.content}")

        print("\n", "CONVERSATIONS", "-" * 80, "\n")
        for advisor_name, conversion in advisory_response.state.conversations.items():
            for message in conversion:
                print("\n", advisor_name, "-" * 40)
                print(f"{message.__class__.__name__} {message.name}: {message.content}")

        print("\n", "SIGNALS", "-" * 80, "\n")
        for advisor_name, signal in advisory_response.state.signals.items():
            print(
                "\n"
                f"Advisor: '{advisor_name}'"
                f" Signal: '{signal.signal}'"
                f" Confidence: '{signal.confidence}'"
                f" Reasoning: '{signal.reasoning}'"
                "\n"
            )

        print(
            "-" * 80,
            "\n",
            advisory_response.state.messages[0].content,
            "\n",
            "\n",
            advisory_response.advice,
            "\n",
            "-" * 80,
            "\n\n",
        )

    def notify_trade(self, trade):
        print(trade)


class RSIRollercoasterStrategy(bt.Strategy):
    """
    Trading Ruleset:

    Indicators:

        RSI Calculation:

            Use a 14-period RSI to determine overbought and
            oversold conditions.

        Simple Moving Average (SMA):

            Use a 200-period Simple Moving Average to ensure we
            trade in the direction of the long-term trend.

        Average True Range (ATR):

            Use a 14-period ATR to gauge market volatility.

    Entry Rules:

        Buy (Long Position):

            Enter a long position when the RSI crosses
            above 30 (indicating oversold conditions).
            Ensure the closing price is above the 200-period SMA
            to confirm an overall uptrend.

        Sell (Short Position):

            Enter a short position when RSI crosses
            below 70 (indicating overbought conditions).
            Ensure the closing price is below the 200-period SMA
            to confirm an overall downtrend.

    Exit Rules:

        Long Position Exit:

            Exit the position when RSI crosses below 50 (indicating
            a reversion towards neutral territory).
            Alternatively, exit the position if the profit target (e.g., 1% gain)
            or stop loss (e.g., 1% loss) is met.

        Short Position Exit:

            Exit the position when RSI crosses above 50 (indicating
            a reversion towards neutral territory).
            Alternatively, exit the position if the profit target (e.g., 1% gain)
            or stop loss (e.g., 1% loss) is met.

    Additional Filters:

        Intratrade Checks:

            Volatility Check: Ensure that during the trade, the
            current market's ATR value does not exceed a certain
            threshold to avoid high volatility conditions.

            Time of Day Filter:

            Restrict trading to specific times of the day,
            avoiding low liquidity periods (e.g., avoid trading
            during lunch hours or major news announcements).
    """

    params = {
        "rsi_period": 11,
        "rsi_low": 40,
        "rsi_high": 56,
        "rsi_mid": 71,
        "sma_period": 130,
        "atr_period": 17,
        "profit_target": 0.02,  # 2% profit target
        "stop_loss": 0.02,  # 2% stop loss
    }

    def __init__(self):
        bot_advisory.init_strategy(self)
        self.close_price = self.datas[0].close
        self.order = None
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.datas[0], period=self.params.rsi_period
        )
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_period
        )
        self.atr = bt.indicators.AverageTrueRange(
            self.datas[0], period=self.params.atr_period
        )

        self.entry_price = None
        self.lastlen = -1

    def next(self) -> None:
        if (
            hasattr(self.data, "isdelayed") and self.data.isdelayed()
        ):  # prevents from live trading on delayed data
            return
        if self.lastlen == len(self.data):
            return
        self.lastlen = len(self.data)
        if self.order:  # check if there's any open order
            return

        if not self.position:  # not in the market
            if self.rsi[0] < self.p.rsi_low and self.close_price[0] > self.sma[0]:
                advisory = bot_advisory.get_advisory(
                    "I see a buy signal, please confirm"
                )
                if advisory.advice.signal == "buy":
                    self.log(f"Creating BUY order @ {self.close_price[0]}")
                    self.entry_price = self.close_price[0]
                    self.order = self.buy(size=0.01)
                else:
                    print("No long confirmation, skipping")
                self.print_advisory_response(advisory)
            elif self.rsi[0] > self.p.rsi_high and self.close_price[0] < self.sma[0]:
                advisory = bot_advisory.get_advisory(
                    "I see a sell signal, please confirm"
                )
                if advisory.advice.signal == "sell":
                    self.log(f"Creating SELL order @ {self.close_price[0]}")
                    self.entry_price = self.close_price[0]
                    self.order = self.sell(size=0.01)
                else:
                    print("No short confirmation, skipping")
                self.print_advisory_response(advisory)
        else:  # in the market
            if self.position.size > 0:  # long position
                if (
                    self.rsi[0] > self.p.rsi_mid
                    or self.close_price[0]
                    >= self.entry_price * (1 + self.params.profit_target)
                    or self.close_price[0]
                    <= self.entry_price * (1 - self.params.stop_loss)
                ):
                    advisory = bot_advisory.get_advisory(
                        "I see a close signal, please confirm"
                    )
                    if advisory.advice.signal in ["sell", "close"]:
                        self.log(f"Closing LONG position @ {self.close_price[0]}")
                        self.order = self.close()
                    else:
                        print("No long close confirmation, skipping")
                    self.print_advisory_response(advisory)
            elif self.position.size < 0:  # short position
                if (
                    self.rsi[0] < self.p.rsi_mid
                    or self.close_price[0]
                    <= self.entry_price * (1 - self.params.profit_target)
                    or self.close_price[0]
                    >= self.entry_price * (1 + self.params.stop_loss)
                ):
                    advisory = bot_advisory.get_advisory(
                        "I see a close signal, please confirm"
                    )
                    if advisory.advice.signal in ["buy", "close"]:
                        self.log(f"Closing SHORT position @ {self.close_price[0]}")
                        self.order = self.close()
                    else:
                        print("No short close confirmation, skipping")
                    self.print_advisory_response(advisory)

    def print_advisory_response(self, advisory_response, print_all=False):
        print(self.datetime.datetime(), "UTC")
        if print_all:
            print("\n", "ADDITIONAL DATA", "-" * 80, "\n")
            print(advisory_response.state.data)

            print("\n", "MESSAGES", "-" * 80, "\n")
            for message in advisory_response.state.messages:
                print(f"{message.__class__.__name__} {message.name}: {message.content}")

            print("\n", "CONVERSATIONS", "-" * 80, "\n")
            for (
                advisor_name,
                conversion,
            ) in advisory_response.state.conversations.items():
                for message in conversion:
                    print("\n", advisor_name, "-" * 40)
                    print(
                        f"{message.__class__.__name__} {message.name}: {message.content}"
                    )

        print("\n", "SIGNALS", "-" * 80, "\n")
        for advisor_name, signal in advisory_response.state.signals.items():
            print(
                "\n"
                f"Advisor: '{advisor_name}'"
                f" Signal: '{signal.signal}'"
                f" Confidence: '{signal.confidence}'"
                f" Reasoning: '{signal.reasoning}'"
                "\n"
            )

        print(
            "-" * 80,
            "\n",
            advisory_response.state.messages[0].content,
            "\n",
            "\n",
            advisory_response.advice,
            "\n",
            "-" * 80,
            "\n\n",
        )

    def notify_order(self, order: bt.Order) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [
            order.Completed,
            order.Canceled,
            order.Margin,
            order.Rejected,
        ]:
            self.order = None

    def notify_trade(self, trade: bt.Trade) -> None:
        if not trade.isclosed:
            return
        self.log(f"OPERATION PROFIT, GROSS {trade.pnl}, NET {trade.pnlcomm}")

    # Define a helper function to include date/time in logs
    def log(self, txt: str) -> None:
        dt = self.data.datetime.date(0)
        t = self.data.datetime.time(0)
        print(f"{dt} {t} {txt}")


def create_cerebro():

    config = dotenv_values()

    cerebro = bt.Cerebro(quicknotify=True, stdstats=False)
    broker = TLBackBroker(
        environment=config.get("tl_environment", "demo"),
        username=config.get("tl_email", ""),
        password=config.get("tl_password", ""),
        server=config.get("tl_server", ""),
        acc_num=int(config.get("tl_acc_num", 0)),
        log_level="info",
        disk_cache_location="./dc",
        # convert_currencies=True,
        # convert_currencies_cache_resolution=60,
        # quicknotify=True,
    )
    cerebro.setbroker(broker)

    # create data
    # from and to date to fetch historical data only
    from_date = datetime(2025, 4, 1, 0, 0, 0, 0, UTC)
    to_date = datetime(2025, 4, 4, 0, 0, 0, 0, UTC)

    timeframe = bt.TimeFrame.Minutes
    compression = 5
    compression_1 = 30
    data = TLData(
        dataname="BTCUSD",
        timeframe=timeframe,
        compression=compression,
        fromdate=from_date.replace(tzinfo=None),
        todate=to_date.replace(tzinfo=None),
        # num_prefill_candles=400,
        # start_live_data=True,
    )
    # when data switches to live, ticks will be used, either resampledata or replaydata
    cerebro.resampledata(data, timeframe=timeframe, compression=compression)
    cerebro.resampledata(data, timeframe=timeframe, compression=compression_1)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addstrategy(RSIRollercoasterStrategy)
    return cerebro


try:
    cerebro = create_cerebro()
    cerebro.run()
except KeyboardInterrupt as e:
    print(e)
finally:
    cerebro.runstop()
    print("Cerebro stopped.")
