import requests

TOKEN = ""
r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates")
print(r.json())
