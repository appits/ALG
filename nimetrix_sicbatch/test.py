
import requests

data = {
   "name": "spResultOrden",
   "param1": "1585",
   "param2": "SE"
}

res = requests.post(url="https://lanta.ingeint.com/api/sp", json=data, timeout=8)

rows = len(res.json())

for rec in res.json():
    print(rec)
