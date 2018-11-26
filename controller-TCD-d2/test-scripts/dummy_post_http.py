import requests
import json
import time
# api-endpoint
URL = "http://127.0.0.1:8080/create-lightpath"

instruction = json.dumps({
    "lightpath": [
        {
            "tx_node": 1,
            "rx_node": 2,
            "status": 0
        }
    ]
})

for i in range(90):
    r = requests.post(url = URL, data = instruction)
    # extracting response text 
    pastebin_url = r.text
    print("The pastebin URL is:%s"%pastebin_url)
    ts = time.time()
    print(ts)
    time.sleep(1)
    ts = time.time()
    print("Then: %s" %ts)

