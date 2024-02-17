import http
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import urllib, base64, uuid, json, httplib2

from yeshualife.payments.tasks import get_the_token
# Create your views here.
reference_id = str(uuid.uuid4())

def apiuser(request,):
    # reference_id = str(uuid.uuid4())
    print(reference_id)
    headers = {
    # Request headers
    'X-Reference-Id': reference_id, #'<put-your-reference-id-here>',
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': 'a247ad4411304f3bb624580ffe0922b9',#'<put-your-primary-subscription-id here>',
  }  
    params = urllib.urlencode({})
    calback_url = 'http://myapp.com/momoapi/callback'
    body = json.dumps({
        "providerCallbackHost":calback_url
    })

    try:
      conn = httplib2.HTTPSConnection('ericssonbasicapi2.azure-api.net')
      conn.request("POST", "/v1_0/apiuser?%s" % params, body, headers)
      response = conn.getresponse()
      print(response.status)
      print(response.reason)
      data = response.read()
      print(data)
      conn.close()
    except Exception as e:
      print("[Errno {0}] {1}".format(e.errno, e.strerror))

####################################
      
def generate_token_task(request):
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
   
    

def generate_api_key(request):
   headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': 'a247ad4411304f3bb624580ffe0922b9'}
   
   calback_url = 'http://myapp.com/momoapi/callback'
   params = urllib.urlencode({ })
   body = json.dumps({"providerCallbackHost": calback_url})
   try:
     conn = httplib2.HTTPSConnection('ericssonbasicapi2.azure-api.net')
     conn.request("POST", "/v1_0/apiuser/${reference_id}/apikey?%s" % params, body, headers)
     response = conn.getresponse()
     print(response.status)
     print(response.reason)
     data = response.read()
     print(data)
     conn.close()
   except Exception as e:
     print("[Errno {0}] {1}".format(e.errno, e.strerror))

####################################
     

def apitoken(request):
   pass

def initiate_payment(request):
    token = ''
    print(apiuser)
    reference_id = ''
    calback_url = 'http://myapp.com/momoapi/callback' #Call back Url
    subscription_key = 'your_subscription_key'

    headers = {
        'Authorization': 'Bearer ' + token,
        'X-Callback-Url': calback_url,
        'X-Reference-Id': reference_id,
        'X-Target-Environment': 'sandbox',
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
