import requests

TOKEN = "7506486712:AAHslVt5546KBn1kKraWL0EyvIXQ90inU0I"
r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates")
print(r.json())
