from time import sleep

import requests

ctu = True
while ctu:
    try:
        requests.get("http://elasticsearch:9200")
        requests.get("http://redis:6379")
        ctu = False
    except:
        print("无法连接到elasticsearch====================================================================================================================================")
        sleep(1)
        pass
