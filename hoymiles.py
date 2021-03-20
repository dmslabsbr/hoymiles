__author__ = 'dmslabs'

import requests
from requests.models import HTTPBasicAuth, Response, StreamConsumedError
from requests import Request, Session
import hashlib 
from string import Template
import json
import configparser
import logging
import dmslibs
from dmslibs import *
from datetime import datetime, timedelta

# CONFIG Secrets
USER = "user"
PASSWORD = "pass"
PLANT_ID = 00000
SECRETS = 'secrets.ini'

# Contants
VERSAO = '0.01'
MANUFACTURER = 'dmslabs'
APP_NAME = 'HASS.hoymiles'
TOKEN = ''
COOKIE_UID = "'uid=fff9c382-389f-4a47-8dc9-c5486fc3d9f5"
COOKIE_EGG_SESS = "EGG_SESS=XHfAhiHWwU__OUVeKh0IiITBnmwA-IIXEzTCHgHgww6ZYYddOPntPSwVz4Gx7ISbfU0WrvzOLungThcL-9D2KxavrtyPk8Mr2YXLFzJwvM0usPvhzYdt2Y2S9Akt5sjP"
URL1 = "https://global.hoymiles.com/platform/api/gateway/iam/auth_login"
URL2 = "https://global.hoymiles.com/platform/api/gateway/pvm-data/data_count_station_real_data"

PAYLOAD_T1= '''
   {
       "ERROR_BACK":true,
       "LOAD":{
           "loading":true
        },
        "body":{
            "password":"$password",
            "user_name":"$user"
        },
        "WAITING_PROMISE":true
    }
'''

PAYLOAD_T2 = '''
{
    "body": {
        "sid": $sid
    },
    "WAITING_PROMISE": true
}
'''

headers_h1 = {
  'Content-Type': 'application/json',
  'Cookie': '' # 'uid=fff9c382-389f-4a47-8dc9-c5486fc3d9f5; EGG_SESS=XHfAhiHWwU__OUVeKh0IiITBnmwA-IIXEzTCHgHgww6ZYYddOPntPSwVz4Gx7ISbfU0WrvzOLungThcL-9D2KxavrtyPk8Mr2YXLFzJwvM0usPvhzYdt2Y2S9Akt5sjP'
}

headers_h2 = {
  'Content-Type': 'application/json;charset=UTF-8',
  'Cache-Control': 'no-cache',
  'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0',
  'Host': 'global.hoymiles.com',
  'Connection': 'keep-alive',
  'Accept': 'application/json, text/plain, */*',
  'Accept-Encoding': 'gzip, deflate, br',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
  'Accept-Language': 'pt-BR,pt;q=0.9,it-IT;q=0.8,it;q=0.7,es-ES;q=0.6,es;q=0.5,en-US;q=0.4,en;q=0.3',
  'Cookie': 'hm_token_language=en_us; ' # 'uid=fff9c382-389f-4a47-8dc9-c5486fc3d9f5; EGG_SESS=XHfAhiHWwU__OUVeKh0IiITBnmwA-IIXEzTCHgHgww6ZYYddOPntPSwVz4Gx7ISbfU0WrvzOLungThcL-9D2KxavrtyPk8Mr2YXLFzJwvM0usPvhzYdt2Y2S9Akt5sjP'
}

# # GLOBAL VARS
token = ""


def pega_url(url, payload, headers):
    print("Loading: " + url)
    response = requests.request("POST", url, headers=headers, data = payload)
    ret = ""
    if response.status_code != 200:
        print ("erro ao acessar: " + url)
    else:
        ret = response.content
    print("status_code: " + str(response.status_code))
    print("content: " + str(response.content))
    # print("utf8: " + str(response.text.encode('utf8')))
    return ret, response.status_code

def pega_url2(url, payload, headers):
    # não está funcionando , 
    print("Loading: " + url)
    s = Session()
    req = Request('POST', url, data = payload, headers=headers)
    prepped = req.prepare()
    print (prepped.headers)
    #response = requests.request("POST", url, headers=headers, data = payload)
    response = s.send(prepped)
    ret = ""
    if response.status_code != 200:
        print ("erro ao acessar: " + url)
    else:
        ret = response.content
    print("status_code: " + str(response.status_code))
    print("content: " + str(response.content))
    # print("utf8: " + str(response.text.encode('utf8')))
    return ret, response.status_code

def pega_url_jsonDic(url, payload, headers, qualPega):
    # recebe o dic da url
    if qualPega ==1 :
        resposta, sCode = pega_url(url, payload, headers)
    else:
        resposta, sCode = pega_url2(url, payload, headers)
    ret = dict()
    if sCode == 200:
        json_res = json.loads(resposta)
        ret = json_res
    return ret

def pega_token():
   # pega o token
   global token
   global TOKEN

   pass_hash = hashlib.md5(PASSWORD.encode()) # b'GeeksforGeeks' 
   pass_hex = pass_hash.hexdigest()
   print(pass_hex) 
   ret = False
   T1 = Template(PAYLOAD_T1)
   payload_T1 = T1.substitute(user = USER, password = pass_hex)
   print(payload_T1)
   header = headers_h1
   header['Cookie'] = "'" + COOKIE_UID + "; " + COOKIE_EGG_SESS + "'"
   login, sCode = pega_url(URL1, payload_T1, header)
   if sCode == 200:
      json_res = json.loads(login)
      if json_res['status'] == '0':
        data_body = json_res['data']
        token = json_res['data']['token']
        TOKEN = token
        ret = True
        if token == "":
            print ('erro na resposta')
            ret = False
   return ret

def pega_solar(uid):
    # pega dados da usina
    ret = False
    T2 = Template(PAYLOAD_T2)
    payload_t2 = T2.substitute(sid = uid)
    header = headers_h2
    header['Cookie'] = COOKIE_UID + "; " + COOKIE_EGG_SESS + "; hm_token=" + token + "; Path=/; Domain=.global.hoymiles.com; Expires=Sat, 19 Mar 2022 22:11:48 GMT;" + "'"
    solar = pega_url_jsonDic(URL2, payload_t2, header, 2)
    if solar['status'] != 0:
        ret = solar['status']
    if solar['status'] == "100":
        # erro no token
        # pede um novo  
        if (pega_token()):
            # chama pega solar novamente
            ret = pega_solar(uid)
    return ret

def get_secrets():
    ''' GET configuration data '''
    global USER
    global PASSWORD
    global PLANT_ID

    config = getConfigParser(SECRETS)

    print ("Reading secrets.ini")

    # le os dados
    USER  = get_config(config, 'secrets', 'MQTT_USER', USER)
    PASSWORD = get_config(config, 'secrets', 'MQTT_PASS', PASSWORD)
    PLANT_ID = get_config(config, 'config','INTERVALO_MQTT', PLANT_ID, getInt=True)
   



# INICIO, START

print (Color.B_Blue + "********** " + MANUFACTURER + " " + APP_NAME + " v." + VERSAO + Color.B_Default)
print (Color.B_Green + "Starting up... " + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + Color.B_Default)

inicia_log(logFile='/var/tmp/hass.hoymiles.log', logName='hass.hoymiles', stdOut=True)
get_secrets()

pegou = False
if TOKEN == '':
    pegou = pega_token()
else:
    token = TOKEN

if token != '':
    # pega dados solar
    dados_solar = pega_solar(PLANT_ID)
    print (str(dados_solar))
 





'''

sudo pip3 install requests

'''






