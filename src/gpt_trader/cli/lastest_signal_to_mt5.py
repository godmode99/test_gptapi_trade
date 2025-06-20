"""Send the most recent parsed signal to MetaTrader5."""

import json
import re
import MetaTrader5 as mt5

# Map signal prefixes to the actual MT5 symbol names.  Brokers sometimes use
# slightly different naming conventions for the same instrument.  Adjust this
# mapping to suit your trading terminal.
SYMBOL_MAP = {
    "XAUUSDM": "XAUUSDm",
    "XAUUSD": "XAUUSDm",  # GPT may omit the trailing 'm'
}

class TradeSignalSender:
    def __init__(self, signal_path: str, symbol_map: dict | None = None):
        self.signal_path = signal_path
        self.signal = self.load_signal()
        self.symbol_base = self.extract_symbol_base()
        self.symbol_map = {k.upper(): v for k, v in (symbol_map or SYMBOL_MAP).items()}
        self.symbol = None
        self.entry = None
        self.sl = None
        self.tp = None
        self.lot = None
        self.rr = None
        self.confidence = None
        self.max_drawdown = None
        self.pending_order_type = None
        self.order_type = None
        self.balance = None

        self.process()

    def load_signal(self):
        with open(self.signal_path, "r") as f:
            return json.load(f)

    def extract_symbol_base(self):
        match = re.match(r"^([a-zA-Z]+)", self.signal["signal_id"])
        if not match:
            raise ValueError(f"❌ Cannot extract symbol from signal_id: {self.signal['signal_id']}")
        return match.group(1).upper()

    def find_matching_symbol(self, base: str):
        base_up = base.upper()
        mapped = self.symbol_map.get(base_up)
        if mapped:
            return mapped
        for sym in mt5.symbols_get():
            if sym.name.upper().startswith(base_up):
                return sym.name
        return None

    def calculate_risk_reward(self):
        self.rr = 1 + (100 - self.confidence) / 50
        if "buy" in self.pending_order_type:
            self.tp = self.entry + (self.entry - self.sl) * self.rr
        else:
            self.tp = self.entry - (self.sl - self.entry) * self.rr

    def calculate_lot(self, balance):
        risk_pct = self.max_drawdown / 10
        risk_amount = balance * (risk_pct / 100)
        sl_distance = abs(self.entry - self.sl)
        pip_value = 10
        lot = risk_amount / (sl_distance * pip_value)
        return round(lot, 2)

    def prepare_order_type(self):
        type_map = {
            "buy_limit": mt5.ORDER_TYPE_BUY_LIMIT,
            "sell_limit": mt5.ORDER_TYPE_SELL_LIMIT,
            "buy_stop": mt5.ORDER_TYPE_BUY_STOP,
            "sell_stop": mt5.ORDER_TYPE_SELL_STOP,
        }
        self.order_type = type_map.get(self.pending_order_type)
        if self.order_type is None:
            raise ValueError(f"❌ Invalid pending_order_type: {self.pending_order_type}")

    def adjust_entry_if_needed(self, market_price, point):
        min_diff = point * 50
        if self.order_type in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_SELL_LIMIT]:
            if (self.order_type == mt5.ORDER_TYPE_BUY_LIMIT and self.entry >= market_price) or \
               (self.order_type == mt5.ORDER_TYPE_SELL_LIMIT and self.entry <= market_price):
                print(f"⚠️ Adjusting invalid entry {self.entry}")
                self.entry = market_price - min_diff if "buy" in self.pending_order_type else market_price + min_diff
        elif self.order_type in [mt5.ORDER_TYPE_BUY_STOP, mt5.ORDER_TYPE_SELL_STOP]:
            if (self.order_type == mt5.ORDER_TYPE_BUY_STOP and self.entry <= market_price) or \
               (self.order_type == mt5.ORDER_TYPE_SELL_STOP and self.entry >= market_price):
                print(f"⚠️ Adjusting invalid entry {self.entry}")
                self.entry = market_price + min_diff if "buy" in self.pending_order_type else market_price - min_diff

    def process(self):
        if not mt5.initialize():
            raise RuntimeError("❌ MT5 initialize failed")

        self.symbol = self.find_matching_symbol(self.symbol_base)
        if not self.symbol:
            mt5.shutdown()
            raise RuntimeError(f"❌ Symbol '{self.symbol_base}' not found!")

        if not mt5.symbol_select(self.symbol, True):
            mt5.shutdown()
            raise RuntimeError(f"❌ Cannot select symbol {self.symbol}")

        tick = mt5.symbol_info_tick(self.symbol)
        info = mt5.symbol_info(self.symbol)
        account = mt5.account_info()
        if not tick or not info or not account:
            mt5.shutdown()
            raise RuntimeError("❌ Cannot retrieve market/account data")

        self.balance = account.balance
        self.entry = float(self.signal["entry"])
        self.sl = float(self.signal["sl"])
        self.confidence = int(self.signal.get("confidence", 70))
        self.max_drawdown = float(self.signal.get("max_drawdown", 20))
        self.pending_order_type = self.signal["pending_order_type"].lower().replace(" ", "_")

        self.calculate_risk_reward()
        self.lot = self.calculate_lot(self.balance)
        self.prepare_order_type()

        market_price = tick.ask if "buy" in self.pending_order_type else tick.bid
        self.adjust_entry_if_needed(market_price, info.point)

        order = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": self.symbol,
            "volume": self.lot,
            "type": self.order_type,
            "price": self.entry,
            "sl": self.sl,
            "tp": self.tp,
            "deviation": 10,
            "magic": 888888,
            "comment": self.signal["signal_id"],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

        print(f"\n📤 Sending order for {self.symbol} ({self.signal['signal_id']})")
        print(f"→ Confidence: {self.confidence}, RR: {self.rr:.2f}")
        print(f"→ Entry: {self.entry}, SL: {self.sl}, TP: {self.tp}")
        print(f"→ Lot: {self.lot}, Balance: ${self.balance:.2f}\n")

        result = mt5.order_send(order)
        if result is None:
            print("❌ order_send returned None")
            print("MT5 last error:", mt5.last_error())
        elif result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Order failed [{result.retcode}]:", result.comment)
        else:
            print(f"✅ Order sent successfully for {self.symbol}")

        mt5.shutdown()
