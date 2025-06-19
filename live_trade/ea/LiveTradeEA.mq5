#property strict
#include <Trade/Trade.mqh>
#include "RiskUtils.mqh"

//+------------------------------------------------------------------+
//| Expert Advisor to execute live trade signals from CSV             |
//| Adjust SignalsFile and DefaultRisk as needed.                     |
//| Expected CSV columns:                                             |
//| timestamp,entry,sl,tp,pending_order_type,confidence               |
//+------------------------------------------------------------------+
input string SignalsFile = "data/live_trade/signals/signals_csv/csv_signal_report.csv"; // CSV path
input double DefaultRisk = 0.01;  // 1% default risk

CTrade trade;

struct Signal
  {
   datetime timestamp;
   double   entry;
   double   sl;
   double   tp;
   string   type;
   double   conf;
  };

static datetime last_processed = 0;

bool LoadLatestSignal(Signal &sig)
  {
   int handle = FileOpen(SignalsFile, FILE_READ|FILE_TXT);
   if(handle == INVALID_HANDLE)
      return(false);

   string line="";
   while(!FileIsEnding(handle))
      line=FileReadString(handle);
   FileClose(handle);

   string parts[];
   if(StringSplit(line,',',parts)<6)
      return(false);

   sig.timestamp = (datetime)StringToTime(parts[0]);
   sig.entry     = StringToDouble(parts[1]);
   sig.sl        = StringToDouble(parts[2]);
   sig.tp        = StringToDouble(parts[3]);
   sig.type      = parts[4];
   sig.conf      = StringToDouble(parts[5]);
   return(true);
  }



void OnTick()
  {
   static datetime last_bar=0;
   datetime curbar=iTime(_Symbol,_Period,0);
   if(curbar==last_bar)
      return;
   last_bar=curbar;

   Signal sig;
   if(!LoadLatestSignal(sig))
      return;
   if(sig.timestamp==last_processed)
      return;
   last_processed=sig.timestamp;

   double lot=CalcLot(sig.entry,sig.sl,sig.conf);
   if(lot<=0) return;

   MqlTradeRequest req; MqlTradeResult res;
   ZeroMemory(req); ZeroMemory(res);
   req.action=TRADE_ACTION_PENDING;
   req.symbol=_Symbol;
   req.price=sig.entry;
   req.sl=sig.sl;
   req.tp=sig.tp;
   req.volume=lot;
   req.type_filling=ORDER_FILLING_RETURN;

   if(sig.type=="buy_limit") req.type=ORDER_TYPE_BUY_LIMIT;
   else if(sig.type=="sell_limit") req.type=ORDER_TYPE_SELL_LIMIT;
   else if(sig.type=="buy_stop") req.type=ORDER_TYPE_BUY_STOP;
   else if(sig.type=="sell_stop") req.type=ORDER_TYPE_SELL_STOP;
   else return;

   OrderSend(req,res);
  }
//+------------------------------------------------------------------+
