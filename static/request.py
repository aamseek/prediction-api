import requests
import json

# local url
url = 'http://127.0.0.1:5000' # change to your url


# sample data
data = {'lead_id': 70982}

data = json.dumps(data)

send_request = requests.post(url, data)

print(send_request)

print(send_request.json())

