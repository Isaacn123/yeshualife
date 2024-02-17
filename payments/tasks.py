import http
from background_task import background

@background(schedule=60)
def get_the_token():
    # get token logic code
    conn = http.client.HTTPSConnection("sandbox.momodeveloper.mtn.com")
    payload = ''
    headers = {
    'Ocp-Apim-Subscription-Key': 'd7d2a50561a34050977f2a5504cadc49',
    'Authorization': 'Basic YWQ5NzIyMjUtMDAzYS00YmZiLTkzMmUtMTc5YjVkNDYxZDI0OjBmYTdjNzM0NjM0ZDQ3MDRiYWY0Y2I1NzUyNDNhMzhk'
    }
    conn.request("POST", "/collection/token/", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))