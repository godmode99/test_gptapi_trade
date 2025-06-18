#ifndef JSON_PARSER_MQH
#define JSON_PARSER_MQH

#include <stdlib.mqh>

class JsonParser
  {
private:
   string m_text;
public:
   bool Parse(const string text)
     {
      m_text=text;
      return(true);
     }

   string GetString(const string key) const
     {
      string pattern="\""+key+"\"";
      int pos=StringFind(m_text,pattern);
      if(pos==-1) return "";
      pos=StringFind(m_text,":",pos);
      if(pos==-1) return "";
      pos++;
      bool quoted=false;
      while(pos<StringLen(m_text) && (m_text[pos]==' ' || m_text[pos]=='\"'))
        {
         if(m_text[pos]=='\"')
           {
            quoted=true;
            pos++;
            break;
           }
         pos++;
        }
      int end=pos;
      if(quoted)
        {
         end=StringFind(m_text,"\"",pos);
         if(end==-1) end=StringLen(m_text);
         return StringSubstr(m_text,pos,end-pos);
        }
      while(end<StringLen(m_text) && m_text[end]!=',' && m_text[end]!='}' && m_text[end]!=' ' && m_text[end]!='\n' && m_text[end]!='\r')
         end++;
      return StringSubstr(m_text,pos,end-pos);
     }

   double GetDouble(const string key) const
     {
      return StringToDouble(GetString(key));
     }
  };

#endif // JSON_PARSER_MQH
