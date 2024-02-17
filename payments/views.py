import http
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import urllib, base64, uuid, json, httplib2
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import requests
from rest_framework import status
from rest_framework.views import APIView

# Create your views here.
reference_id = str(uuid.uuid4())


class GetTheTokenAPIView(APIView):

    def post(self, request):
        api_token = self.generate_api_token(request=request)


        if api_token:
            access_token = self.extract_api_token_key(api_token)

            return access_token
    
    def extract_api_token_key(self, response_data):
        try:
            response_content = response_data.content.decode('utf-8')
            response_json = json.loads(response_content)
            access_token = response_json.get('access_token')
            if access_token:
                return HttpResponse(access_token)
            else:
                return HttpResponse("No Access Token Found")
            
        except json.JSONDecodeError as e:
            return HttpResponse({'error': str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)

    def generate_api_token(self,request):

        if request.method == "POST":
            payload = {}
            headers = {
            'Ocp-Apim-Subscription-Key': 'd7d2a50561a34050977f2a5504cadc49',
            'Authorization': 'Basic YWQ5NzIyMjUtMDAzYS00YmZiLTkzMmUtMTc5YjVkNDYxZDI0OjBmYTdjNzM0NjM0ZDQ3MDRiYWY0Y2I1NzUyNDNhMzhk'
            }
            try:
                conn = http.client.HTTPSConnection("sandbox.momodeveloper.mtn.com")
                conn.request("POST", "/collection/token/", payload, headers)

                # Get the response
                res = conn.getresponse()

                # Read response
                data = res.read()

                # Print Decoded Response
                print(data.decode("utf-8"))

                conn.close()

                # Return response
                return HttpResponse(data, status=status.HTTP_200_OK)
            
                # response = requests.request("POST", url, headers=headers, data=payload)
                # print(response.text)
            except Exception as e:
                # Handle any exceptions that occur during the request
                return HttpResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Handle non-POST requests
            return HttpResponse({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def make_request_to_pay(self,api_token):
        pass



class RequestToPayAPIView(APIView):
    def post(self,request):

        api_access_token = GetTheTokenAPIView

        if request.method =="POST":
                conn = http.client.HTTPSConnection("sandbox.momodeveloper.mtn.com")
                payload = json.dumps({
                "amount": "1.0",
                "currency": "EUR",
                "externalId": "09898687",
                "payer": {
                    "partyIdType": "MSISDN",
                    "partyId": "0700186921"
                },
                "payerMessage": "Helli am testing here",
                "payeeNote": "Thank you for your Generousty"
                })

                headers = {
                'Ocp-Apim-Subscription-Key': 'd7d2a50561a34050977f2a5504cadc49',
                'X-Reference-Id': '169c8982-99e1-4799-be51-d8c98881cc8e',
                'X-Target-Environment': 'sandbox',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSMjU2In0.eyJjbGllbnRJZCI6ImFkOTcyMjI1LTAwM2EtNGJmYi05MzJlLTE3OWI1ZDQ2MWQyNCIsImV4cGlyZXMiOiIyMDI0LTAyLTE3VDAwOjAzOjA5LjgyNSIsInNlc3Npb25JZCI6IjhkY2Q1MDE3LTZmYzYtNGJiZS04ZDMyLTZkMmZmOTNkZmJjZiJ9.Qq1rW1KHcC2Sy0m8ZFUqG9xlNiVrjCdpn1yfEzm2S_MHz3Vru_8r0PuycIKhbzNEB-aBmvQ_uovIwPsfM6Z6KTUH6r-Iov_9408dw99UjsR8nvI7aPvw1Fi1UuxQSkU3L_06rXxRolpdydZD_OkciYzs35IWmBi68vav7IjDtgmmqJ9VGgRz3CdL75KC5rHD5IOxOdNzDxJSyB6DxHx1ZA4B611Bo1UbXa2r6V7YspTv5278vMCMgVskeqcfjoDbutMkhChKAgt5Fi2Mq8TU3QH72x40v53D7f79rpR4FnCcqIJYufzRkh3Kh_0eBf3wWJDp9KgwVo4aIDM_COhOZA'
                }

                try:

                    conn.request("POST", "/collection/v1_0/requesttopay", payload, headers)
                    res = conn.getresponse()
                    data = res.read()
                    print(data.decode("utf-8"))

                    return HttpResponse({"data": data}, status=status.HTTP_201_CREATED)
                
                except Exception as e:
                    return HttpResponse({"error":"Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR);
        else:
            return HttpResponse({"error":"Method not allowed!"}, status= status.HTTP_405_METHOD_NOT_ALLOWED)
        
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

def get_data(request):
    return HttpResponse("Hello World")


# @csrf_exempt   
def generate_token_task(request):

    # if request.method == 'POST':
        # get token logic code
        payload = {}
        headers = {
        'Ocp-Apim-Subscription-Key': 'd7d2a50561a34050977f2a5504cadc49',
        'Authorization': 'Basic YWQ5NzIyMjUtMDAzYS00YmZiLTkzMmUtMTc5YjVkNDYxZDI0OjBmYTdjNzM0NjM0ZDQ3MDRiYWY0Y2I1NzUyNDNhMzhk'
        }

        try:
            url = "https://sandbox.momodeveloper.mtn.com/collection/token/"
            # conn = http.client.HTTPSConnection("sandbox.momodeveloper.mtn.com")
            # conn.request("POST", "/collection/token/", payload, headers)

            # Get the response
            # res = conn.getresponse()

            #Read response
            # data = res.read()

            # Print Decoded Response
            # print(data.decode("utf-8"))

            # conn.close()
            # response = requests.request("POST", url, headers=headers, data=payload)
            # print(response.text)

            return HttpResponse("HEllo World")


        except Exception as e:
            # Handle any exceptions that occur during the request
            print("An error occurred:", e)
    # else:
        # Handle non-POST requests
        # return HttpResponse("Method not allowed", status=405)
   
    

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
