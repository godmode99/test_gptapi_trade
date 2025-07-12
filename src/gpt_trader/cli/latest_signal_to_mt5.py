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
    def __init__(
        self,
        signal_path: str,
        symbol_map: dict | None = None,
        risk_per_trade: float | None = None,
        max_risk_per_trade: float | None = None,
    ):
        self.signal_path = signal_path
        self.signal = self.load_signal()
        self.pending_order_type = (
            str(self.signal.get("pending_order_type", ""))
            .lower()
            .replace(" ", "_")
        )
        if self.pending_order_type != "skip":
            self.symbol_base = self.extract_symbol_base()
        else:
            self.symbol_base = None
        merged_map = {**SYMBOL_MAP, **(symbol_map or {})}
        self.symbol_map = {k.upper(): v for k, v in merged_map.items()}
        self.symbol = None
        self.entry = None
        self.sl = None
        self.tp = None
        self.lot = None
        self.rr = None
        self.confidence = None
        self.max_drawdown = None
        self.risk_per_trade = risk_per_trade
        self.max_risk_per_trade = max_risk_per_trade
        self.order_type = None
        self.balance = None
        self.order_result = None
        self.adjust_note = None

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
        """Calculate risk/reward based on entry, SL, and TP distances."""
        risk = abs(self.entry - self.sl)
        reward = abs(self.tp - self.entry)
        if risk == 0:
            raise ValueError("SL must not equal entry when computing RR")
        self.rr = reward / risk

    def calculate_lot(self, balance, tick_value, tick_size, volume_min,
                      volume_max, volume_step):
        if self.risk_per_trade <= 0:
            raise ValueError("risk_per_trade must be positive")

        sl_distance = abs(self.entry - self.sl)
        if sl_distance == 0:
            raise ValueError("SL must not equal entry")

        pip_value = tick_value / tick_size if tick_size else 10
        risk_amount = balance * (self.risk_per_trade / 100)
        lot = risk_amount / (sl_distance * pip_value)

        # align to broker limits
        lot = max(volume_min, min(volume_max, lot))
        steps = round(lot / volume_step)
        lot = steps * volume_step
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

    def _adjust_order_type(self, tick) -> None:
        """Ensure ``pending_order_type`` matches the current price."""
        ask = getattr(tick, "ask", None)
        bid = getattr(tick, "bid", None)
        if ask is None or bid is None:
            return

        orig = self.pending_order_type
        if orig == "buy_stop" and self.entry <= ask:
            self.pending_order_type = "buy_limit"
        elif orig == "buy_limit" and self.entry >= ask:
            self.pending_order_type = "buy_stop"
        elif orig == "sell_stop" and self.entry >= bid:
            self.pending_order_type = "sell_limit"
        elif orig == "sell_limit" and self.entry <= bid:
            self.pending_order_type = "sell_stop"

        if self.pending_order_type != orig:
            print(f"↩️ Adjusting order type from {orig} to {self.pending_order_type}")
            self.adjust_note = f"adjust:{orig}->{self.pending_order_type}"


    def process(self):
        raw_conf = self.signal.get("confidence")
        try:
            self.confidence = (
                float(str(raw_conf).rstrip("%")) if raw_conf is not None else None
            )
        except (TypeError, ValueError):
            self.confidence = None

        if self.pending_order_type == "skip":
            reason = self.signal.get("short_reason", "")
            print(f"⏭️ Skipping signal {self.signal['signal_id']} {reason}")
            self.max_drawdown = self.signal.get("max_drawdown")
            if self.max_risk_per_trade is not None:
                conf = self.confidence or 0
                self.risk_per_trade = min(
                    self.max_risk_per_trade,
                    (float(conf) / 100) * float(self.max_risk_per_trade),
                )
            elif self.risk_per_trade is None:
                self.risk_per_trade = self.signal.get("risk_per_trade")
            self.order_result = "skipped"
            return

        if self.confidence == 0:
            reason = self.signal.get("short_reason", "")
            print(f"⏭️ Skipping signal {self.signal['signal_id']} {reason}")
            self.max_drawdown = self.signal.get("max_drawdown")
            if self.max_risk_per_trade is not None:
                conf = self.confidence or 0
                self.risk_per_trade = min(
                    self.max_risk_per_trade,
                    (float(conf) / 100) * float(self.max_risk_per_trade),
                )
            elif self.risk_per_trade is None:
                self.risk_per_trade = self.signal.get("risk_per_trade")
            self.order_result = "confidence=0"
            return

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
        if "tp" not in self.signal:
            mt5.shutdown()
            raise ValueError("❌ 'tp' missing from signal")
        self.tp = float(self.signal["tp"])
        if self.confidence is None:
            self.confidence = int(self.signal.get("confidence", 70))
        else:
            self.confidence = int(self.confidence)
        self.max_drawdown = float(self.signal.get("max_drawdown", 15))
        if self.max_risk_per_trade is not None:
            self.risk_per_trade = min(
                float(self.max_risk_per_trade),
                (self.confidence / 100) * float(self.max_risk_per_trade),
            )
        elif self.risk_per_trade is None:
            self.risk_per_trade = float(
                self.signal.get("risk_per_trade", self.max_drawdown / 10)
            )

        self._adjust_order_type(tick)
        self.prepare_order_type()

        # Use entry and TP values from the GPT response without modification

        self.calculate_risk_reward()
        self.lot = self.calculate_lot(
            self.balance,
            info.trade_tick_value,
            info.trade_tick_size,
            getattr(info, "volume_min", 0.01),
            getattr(info, "volume_max", 100.0),
            getattr(info, "volume_step", 0.01),
        )

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
            last_err = mt5.last_error()
            comment = last_err[1] if isinstance(last_err, tuple) else str(last_err)
            self.order_result = f"error:{comment}"
            print(f"❌ order_send returned None: {comment}")
        elif result.retcode != mt5.TRADE_RETCODE_DONE:
            self.order_result = f"error:{result.comment}"
            print(f"❌ Order failed [{result.retcode}]: {result.comment}")
        else:
            print(f"✅ Order sent successfully for {self.symbol}")
            self.order_result = "success"

        mt5.shutdown()
