"""
Module contain consts and templates used in addon.
"""

import datetime

HTTP_STATUS_CODE = {
    100: "Continue",
    200: "OK",
    202: "Non-Authoritative Information",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    500: "Internal Server Error",
    502: "Bad Gateway",
    504: "Gateway Timeout",
    1000: "Message not set.",
}

MQTT_STATUS_CODE = {
    0: "Connection successful",
    1: "Connection refused – incorrect protocol version",
    2: "Connection refused – invalid client identifier",
    3: "Connection refused – server unavailable",
    4: "Connection refused – bad username or password",
    5: "Connection refused – not authorised",
    100: "Connection refused - other things",
}

PAYLOAD_T1 = """
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
"""

PAYLOAD_T2 = """
{
    "body": {
        "sid": $sid
    },
    "WAITING_PROMISE": true
}
"""

PAYLOAD_ID = """
{
    "body": {
        "id": $id
    },
    "WAITING_PROMISE": true
}
"""

PAYLOAD_DETAILS = """{
    "body":{
        "mi_id":$mi_id,
        "mi_sn":"$mi_sn",
        "port":1,
        "sid":$sid,
        "warn_code":1,
        "time":"$time"
    },
    "WAITING_PROMISE":true
}
"""


HEADER_LOGIN = {"Content-Type": "application/json;charset=UTF-8", "Cookie": ""}

HEADER_DATA = {
    "Content-Type": "application/json;charset=UTF-8",
    "Cache-Control": "no-cache",
    "Host": "global.hoymiles.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",  # pylint: disable=line-too-long
    "Accept-Language": "pt-BR,pt;q=0.9,it-IT;q=0.8,it;q=0.7,es-ES;q=0.6,es;q=0.5,en-US;q=0.4,en;q=0.3",  # pylint: disable=line-too-long
    "Cookie": "hm_token_language=en_us; ",
}

SECRETS = "secrets.ini"

COOKIE_UID = "'uid=fff9c382-389f-4a47-8dc9-c5486fc3d9f5"
COOKIE_EGG_SESS = "EGG_SESS=XHfAhiHWwU__OUVeKh0IiITBnmwA-IIXEzTCHgHgww6ZYYddOPntPSwVz4Gx7ISbfU0WrvzOLungThcL-9D2KxavrtyPk8Mr2YXLFzJwvM0usPvhzYdt2Y2S9Akt5sjP'"  # pylint: disable=line-too-long

BASE_URL = "https://global.hoymiles.com/platform/api/gateway/"
LOGIN_API = "iam/auth_login"
USER_ME = "iam/user_me"
GET_DATA_API = "pvm-data/data_count_station_real_data"
GET_ALL_DEVICE_API = "pvm/station_select_device_of_tree"
STATION_FIND = "pvm/station_find"
DATA_FIND_DETAILS = "pvm-data/data_find_details"
SETTING_BATTERY_CONFIG = "pvm/setting_battery_config"

# For MQTT
MQTT_PUB = "home/solar"
SID = "solar"
MQTT_HASS = "homeassistant"
DEFAULT_MQTT_PASS = "MQTT_PASSWORD"
NODE_ID = "dmslabs"
SHORT_NAME = "solarH"
HASS_INTERVAL = 300
GETDATA_INTERVAL = 480  # How often do I read site data
EXPIRE_TIME = int(GETDATA_INTERVAL) * 1.5


LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


json_hass = {
    "sensor": """
{ 
  "stat_t": "home/$sid/json_$via_device",
  "name": "$name",
  "uniq_id": "$uniq_id",
  "val_tpl": "{{ value_json.$val_tpl }}",
  "icon": "$icon",
  "device_class": "$device_class",
  "state_class": "$state_class",
  "unit_of_measurement": "$unit_of_measurement",
  "expire_after": "$expire_after",
  "device": { $device_dict }
}""",
    "binary_sensor": """
{ 
  "stat_t": "home/$sid/json_$via_device",
  "name": "$name",
  "uniq_id": "$uniq_id",
  "val_tpl": "{{ value_json.$val_tpl }}",
  "icon": "$icon",
  "device_class": "$device_class",
  "device": { $device_dict }
}""",
    "switch": """
{ 
  "stat_t": "home/$sid/json_$via_device",
  "name": "$name",
  "uniq_id": "$uniq_id",
  "val_tpl": "{{ value_json.$val_tpl }}",
  "command_topic": "hoymiles/$via_device/set/$val_tpl",
  "device": { $device_dict }
}""",
    "number": """
{ 
  "stat_t": "home/$sid/json_$via_device",
  "name": "$name",
  "uniq_id": "$uniq_id",
  "min": "$min",
  "max": "$max",
  "val_tpl": "{{ value_json.$val_tpl }}",
  "command_topic": "hoymiles/$via_device/set/$val_tpl",
  "device": { $device_dict }
}""",
}

DEVICE_DICT = """ "name": "$device_name",
    "manufacturer": "$manufacturer",
    "model": "$model",
    "sw_version": "$sw_version",
    "via_device": "$via_device",
    "identifiers": [ "$identifiers" ] """
