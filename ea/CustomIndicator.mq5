#property indicator_separate_window
#property indicator_buffers 3
#property indicator_plots   3

#include <stdlib.mqh>

#property indicator_label1 "RSI14"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrDodgerBlue
#property indicator_width1  2

#property indicator_label2 "SMA20"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrOrange
#property indicator_width2  2

#property indicator_label3 "ATR14"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrRed
#property indicator_width3  2

input bool  DisplaySignals = false;  // Show parsed signals instead of indicators
input string SignalsPath   = "signals"; // Folder with JSON signal files

//--- indicator buffers
double BufferRSI[];
double BufferSMA[];
double BufferATR[];

//--- indicator handles
int rsiHandle=INVALID_HANDLE;
int maHandle=INVALID_HANDLE;
int atrHandle=INVALID_HANDLE;

//--- variables for signal display
string  last_signal_file = "";
struct SignalData
  {
   string id;
   double entry;
   double sl;
   double tp;
   string order_type;
   double confidence;
  };
SignalData current_signal;

int OnInit()
  {
   SetIndexBuffer(0,BufferRSI,INDICATOR_DATA);
   SetIndexBuffer(1,BufferSMA,INDICATOR_DATA);
   SetIndexBuffer(2,BufferATR,INDICATOR_DATA);

   //--- create indicator handles
   rsiHandle = iRSI(_Symbol,PERIOD_CURRENT,14,PRICE_CLOSE);
   maHandle  = iMA(_Symbol,PERIOD_CURRENT,20,0,MODE_SMA,PRICE_CLOSE);
   atrHandle = iATR(_Symbol,PERIOD_CURRENT,14);

   PlotIndexSetString(0,PLOT_LABEL,"RSI14");
   PlotIndexSetString(1,PLOT_LABEL,"SMA20");
   PlotIndexSetString(2,PLOT_LABEL,"ATR14");

   if(DisplaySignals)
      EventSetTimer(10);   // check for signals every 10 seconds

   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   if(DisplaySignals)
      EventKillTimer();

   //--- release indicator handles
   if(rsiHandle!=INVALID_HANDLE)
      IndicatorRelease(rsiHandle);
   if(maHandle!=INVALID_HANDLE)
      IndicatorRelease(maHandle);
   if(atrHandle!=INVALID_HANDLE)
      IndicatorRelease(atrHandle);
  }

void OnTimer()
  {
   if(DisplaySignals)
      LoadLatestSignal();
  }

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
  {
   //--- calculate indicators
   int begin = MathMax(0, rates_total - prev_calculated - 1000);
   double rsi_val[];
   double ma_val[];
   double atr_val[];
   ArrayResize(rsi_val,1);
   ArrayResize(ma_val,1);
   ArrayResize(atr_val,1);
   ArraySetAsSeries(rsi_val,true);
   ArraySetAsSeries(ma_val,true);
   ArraySetAsSeries(atr_val,true);
   for(int i=begin; i<rates_total; i++)
     {
      if(CopyBuffer(rsiHandle,0,i,1,rsi_val)<=0) return(0);
      if(CopyBuffer(maHandle,0,i,1,ma_val)<=0)  return(0);
      if(CopyBuffer(atrHandle,0,i,1,atr_val)<=0) return(0);
      BufferRSI[i] = rsi_val[0];
      BufferSMA[i] = ma_val[0];
      BufferATR[i] = atr_val[0];
     }

   if(DisplaySignals && current_signal.id!="")
     {
      string msg = StringFormat("Signal %s %s\nEntry: %.2f SL: %.2f TP: %.2f Conf: %.0f",
                                current_signal.id,
                                current_signal.order_type,
                                current_signal.entry,
                                current_signal.sl,
                                current_signal.tp,
                                current_signal.confidence);
      Comment(msg);
     }
   else if(!DisplaySignals)
      Comment("");

   return(rates_total);
  }

//--- helper to load latest signal
bool LoadLatestSignal()
  {
   string search = SignalsPath + "/*.json";
   string fname;
   datetime latest=0;
   string latest_file="";
   int handle = FileFindFirst(search,fname);
   if(handle!=INVALID_HANDLE)
      {
       while(fname!="")
         {
         string path_iter = SignalsPath + "/" + fname;
         datetime modify=(datetime)FileGetInteger(path_iter,FILE_MODIFY_DATE);
         if(modify>latest)
           {
            latest=modify;
            latest_file=fname;
           }
         if(!FileFindNext(handle,fname))
            break;
        }
      FileFindClose(handle);
     }
   if(latest_file=="" || latest_file==last_signal_file)
      return(false);
   last_signal_file=latest_file;
   string path = SignalsPath + "/" + latest_file;
   int file=FileOpen(path,FILE_READ|FILE_TXT);
   if(file==INVALID_HANDLE)
      return(false);
   ulong fsize=FileSize(file);
   string content="";
   if(fsize<=2147483647)
     {
      content=FileReadString(file,(int)fsize);
     }
   else
     {
      int chunk=1024*1024;
      while(fsize>0)
        {
         int to_read=(int)MathMin(fsize,chunk);
         content+=FileReadString(file,to_read);
         fsize-=to_read;
        }
     }
   FileClose(file);
   ParseSignal(content,current_signal);
   return(true);
  }

void ParseSignal(string json, SignalData &sig)
  {
   sig.id = GetValue(json,"signal_id");
   sig.entry = StringToDouble(GetValue(json,"entry"));
   sig.sl = StringToDouble(GetValue(json,"sl"));
   sig.tp = StringToDouble(GetValue(json,"tp"));
   sig.order_type = GetValue(json,"pending_order_type");
   sig.confidence = StringToDouble(GetValue(json,"confidence"));
  }

string GetValue(string text,string key)
  {
   string pattern = "\""+key+"\"";
   int pos = StringFind(text,pattern);
   if(pos==-1) return "";
   pos = StringFind(text,":",pos);
   if(pos==-1) return "";
   pos++;
   while(pos<StringLen(text) && (text[pos]==' ' || text[pos]=='\"')) pos++;
   int end=pos;
   while(end<StringLen(text) && text[end]!='\"' && text[end]!=',' && text[end]!='}' && text[end]!='\n' && text[end]!='\r') end++;
   return StringSubstr(text,pos,end-pos);
  }
