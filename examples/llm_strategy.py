import backtrader as bt


from bt_llm_advisory import BacktraderLLMAdvisory


class LLMStrategy(bt.Strategy):
    def __init__(self, bot_advisory: BacktraderLLMAdvisory):
        bot_advisory.init_strategy(self)
        self.bot_advisory = bot_advisory

    def next(self):
        if not self.position:
            # entry signal
            advisory = self.bot_advisory.get_advisory(
                "Provide trading entry signals based on the trend and reversal. You need to provide entry signals to start a new trade. Make sure that the signal is at trend reversals."
            )
            if advisory.advice.signal == "sell":
                self.sell(size=0.01)
            elif advisory.advice.signal == "buy":
                self.buy(size=0.01)
            self.print_advisory_response(advisory, True)

        else:
            # exit signal
            advisory = self.bot_advisory.get_advisory(
                "Provide trading exit signals based on the trend and reversal. You need to provide close signals to end the current trade. Make sure that the signal is at trend reversals."
            )
            if advisory.advice.signal == "close":
                self.close()
            self.print_advisory_response(advisory, True)

    def print_advisory_response(self, advisory_response, print_all=False):
        if len(self.data) < 1:
            return
        print(self.datetime.datetime(0), "UTC")
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
