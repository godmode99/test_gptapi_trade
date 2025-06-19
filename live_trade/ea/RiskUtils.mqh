#ifndef RISK_UTILS_MQH
#define RISK_UTILS_MQH

//+------------------------------------------------------------------+
//| Calculate lot size from entry, sl and confidence                 |
//| Uses DefaultRisk (input double) defined in the including EA      |
//+------------------------------------------------------------------+
inline double CalcLot(double entry,double sl,double confidence)
  {
   double risk=DefaultRisk;
   if(confidence>80) risk=0.05;
   else if(confidence>70) risk=0.03;

   double distance=MathAbs(entry-sl);
   if(distance<=0) return(0);

   double tick_value=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
   double lots=(AccountInfoDouble(ACCOUNT_BALANCE)*risk)/(distance/_Point*tick_value);

   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double minv=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   lots=MathMax(lots,minv);
   lots=MathFloor(lots/step)*step;
   return(lots);
  }

#endif // RISK_UTILS_MQH
