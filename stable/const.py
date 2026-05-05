"""
Module contain consts and templates used in addon.
"""

import datetime

BASE_URL = "https://neapi.hoymiles.com"
LOGIN_API = "/iam/pub/0/auth/login"
USER_ME = "/iam/pub/0/user/user_me"
GET_DATA_API = "/pvm-data/api/0/station/data/count_station_real_data"
GET_ALL_DEVICE_API = "/pvm/api/0/station/select_device_of_tree"
STATION_FIND = "/pvm/api/0/station/find"
DATA_FIND_DETAILS = "/pvm/api/0/dev/micro/find"
SETTING_BATTERY_CONFIG = "/pvm-ctl/api/0/dev/setting/write"


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


HEADER_LOGIN = {"Content-Type": "application/json"}

HEADER_DATA = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
}

SECRETS = "secrets.ini"

COOKIE_UID = "'uid=fff9c382-389f-4a47-8dc9-c5486fc3d9f5"
COOKIE_EGG_SESS = "EGG_SESS=XHfAhiHWwU__OUVeKh0IiITBnmwA-IIXEzTCHgHgww6ZYYddOPntPSwVz4Gx7ISbfU0WrvzOLungThcL-9D2KxavrtyPk8Mr2YXLFzJwvM0usPvhzYdt2Y2S9Akt5sjP'"  # pylint: disable=line-too-long


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
