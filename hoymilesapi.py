from calendar import month
import logging
import hashlib
from string import Template
import json
import sys
import requests
import time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import uuid

from const import HTTP_STATUS_CODE, COOKIE_UID, COOKIE_EGG_SESS, PAYLOAD_T1, HEADER_LOGIN, HEADER_DATA
from const import BASE_URL, LOGIN_API, GET_DATA_API, PAYLOAD_T2, LOCAL_TIMEZONE, PAYLOAD_ID, GET_ALL_DEVICE_API, USER_ME, STATION_FIND


module_logger = logging.getLogger('HoymilesAdd-on.hoymilesapi')

class PlantObject(object):

    def __init__(self, data:dict) -> None:
        self.id = data['id']
        self.sn = data['sn']
        self.soft_ver = data['soft_ver']
        self.hard_ver = data['hard_ver']
        self.connect = data['warn_data']['connect']
        self.uuid = str(uuid.uuid1())

class Dtu(PlantObject):

    def __init__(self, dtu_data:dict) -> None:
        super(Dtu, self).__init__(dtu_data)
        self.model_no = dtu_data['model_no']


class Micros(PlantObject):

    def __init__(self, micro_data:dict) -> None:
        super(Micros, self).__init__(micro_data)
        self.init_hard_no = micro_data['init_hard_no']


class Hoymiles(object):

    data_dict = {"last_time" : "","load_time": "",
    'load_cnt': 0}
    def __init__(self, plant_id, config, gEnvios, tries = 5) -> None:
        self.plant_id = plant_id
        self.token = None
        self._tries = tries
        self.logger = logging.getLogger('HoymilesAdd-on.hoymilesapi.Hoymiles')
        self.count_station_real_data ={}
        self._config = config
        self.gEnvios = gEnvios
        self.solar_data = {}
        self.load_cnt = 0
        self.dtu = None
        self.device_list = []

        cnt = 0
        while True:
            if not self.get_token():
                self.logger.error("I can't get access token")
                if cnt >= self._tries: 
                    exit()
                time.sleep(60000)
                cnt += 1
            else:
                break

    def get_token(self):
        user = self._config['HOYMILES_USER']
        pass_hash = hashlib.md5(self._config['HOYMILES_PASSWORD'].encode()) # b'senhadohoymiles' 
        pass_hex = pass_hash.hexdigest()

        ret = False
        T1 = Template(PAYLOAD_T1)
        payload_T1 = T1.substitute(user = user, password = pass_hex)
        header = HEADER_LOGIN
        header['Cookie'] = COOKIE_UID + "; " + COOKIE_EGG_SESS
        login, sCode = self.send_post_request(BASE_URL + LOGIN_API, header, payload_T1)
        if sCode == 200:
                json_res = json.loads(login)
                if json_res['status'] == '0':
                    data_body = json_res['data']
                    self.token = json_res['data']['token']
                    ret = True
                    self.logger.info('I got the token!!  :-)')
                    if not self.token:
                        self.logger.error('No response')
                        ret = False
                elif json_res['status'] == '1':
                    self.token = ''
                    self.logger.error('Wrong user/password')
        else:
                self.token = ''
                self.logger.error(f'Wrong user/password {sCode} {HTTP_STATUS_CODE.get(sCode, 1000)}')
        return ret

    def pega_url_jsonDic(self, url, header, payload):
        # recebe o dic da url
        respons, sCode = self.send_request(url, header, payload, 'POST')
        ret = dict()
        if sCode == 200:
            return json.loads(respons)
        return ret

    def send_post_request(self, url, header, payload):
        return self.send_request(url, header, payload, type = 'POST')
        pass

    def send_options_request(self, url, header, payload):
        return self.send_request(url, header, payload, type = 'OPTIONS')
        pass

    def send_request(self, url, header, payload, type):
        self.logger.info(f"Loading: {url}")
        s = requests.Session()
        req = requests.Request("POST", url, headers=header, data = payload.replace('\n',"").encode('utf-8'))
        s = requests.Session()
        prepped = req.prepare()
        self.logger.debug(prepped.headers)
        response = s.send(prepped)
        ret = ""
        if response.status_code != 200:
            self.logger.error(f"Access error: {url}")
            self.logger.error(f"Status code: {response.status_code} {HTTP_STATUS_CODE.get(response.status_code, 1000)}")
        else:
            ret = response.content
            self.logger.debug(f"content: {response.content}")
        return ret, response.status_code


    def get_solar_data(self):
        status, self.solar_data = self.request_solar_data()

        self.data_dict['load_time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self.data_dict['load_cnt'] += 1
        self.solar_data['connect'] = self.dtu.connect

        self.logger.debug(f"solar_data: {self.solar_data}")
        if not self.solar_data['real_power']:
            self.logger.warning("REAL_POWER = 0")
            time.sleep(60) # espera 60 segundos
            self.logger.info("Getting data again")
            status, self.solar_data = self.request_solar_data()
            real_power = int(self.solar_data['real_power'])
        
        capacity = float(self.solar_data['capacitor'])

        if capacity == 0:
            self.logger.error(f"Error capacitor: {capacity}")
        else:
            self.solar_data = self.adjust_solar_data(self.solar_data)
        return self.solar_data

    def adjust_solar_data(self, solar_data):
        real_power = float(solar_data['real_power'])
        capacidade = float(solar_data['capacitor'])
        if capacidade > 0 and capacidade < 100:
            capacidade = capacidade * 1000
        power_ratio = (real_power / capacidade) * 100
        power_ratio = round(power_ratio,1)
        if real_power == 0: 
            self.logger.warning("real_power = 0")

        solar_data['real_power'] = str( real_power )
        solar_data['real_power_measurement'] = str( real_power )
        solar_data['real_power_total_increasing'] = str( real_power )
        solar_data['power_ratio'] = str( power_ratio )
        solar_data['capacitor'] =  str( capacidade )
        solar_data['capacitor_kW'] =  str( capacidade / 1000) 
        co2 = round(float(solar_data['co2_emission_reduction']) / 1000000, 5)
        solar_data['co2_emission_reduction'] = str( co2 )
        solar_data['today_eq_Wh'] = solar_data['today_eq']
        solar_data['today_eq'] = str( round(float(solar_data['today_eq']) / 1000,2) )
        solar_data['month_eq'] = str( round(float(solar_data['month_eq']) / 1000,2) )
        solar_data['year_eq'] = str( round(float(solar_data['total_eq']) / 1000,2) )
        
        last_data_time = solar_data['last_data_time']
        last_data_time = datetime.strptime(last_data_time, '%Y-%m-%d %H:%M:%S')
        solar_data['last_data_time'] = last_data_time.replace(tzinfo=LOCAL_TIMEZONE).isoformat()
        self.logger.info(f"last_data_time {solar_data['last_data_time']}")

        return solar_data

    def request_solar_data(self):
        T2 = Template(PAYLOAD_T2)
        payload_t2 = T2.substitute(sid = self.plant_id)

        header = HEADER_DATA
        header['Cookie'] = COOKIE_UID + "; hm_token=" + self.token + "; Path=/; Domain=.global.hoymiles.com;" + \
            f"Expires=Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;" + "'"

        solar = self.send_payload(GET_DATA_API, header, payload_t2)
        return solar['status'], solar['data']

    def get_plant_hw(self):
        status, hw_data = self.request_plant_hw()
        hw_data = hw_data[0]
        try:
            dtu_data = hw_data['dtu']
            self.dtu = Dtu(dtu_data)
        except Exception as err:
            self.logger.error(f"request_plant_hw dtu {err}")

        if 'micros' in hw_data['repeater_list'][0].keys():
            for micro in hw_data['repeater_list'][0]['micros']:
                self.device_list.append(Micros(micro))
    
    def update_devices_status(self):
        status, hw_data = self.request_plant_hw()
        hw_data = hw_data[0]
        try:
            dtu_data = hw_data['dtu']
            self.dtu.connect = hw_data['dtu']['warn_data']['connect']
        except Exception as err:
            self.logger.error(f"request_plant_hw dtu {err}")
        
        if 'micros' in hw_data['repeater_list'][0].keys():
            for micro in hw_data['repeater_list'][0]['micros']:
                for device in self.device_list:
                    if  micro['sn'] == device.sn:
                        if micro['warn_data']['connect']:
                            device.connect = "ON"
                        else:
                            device.connect = "OFF"
        

    def request_plant_hw(self):
        template = Template(PAYLOAD_ID)
        payload = template.substitute(id = self.plant_id)
        header = HEADER_DATA
        header['Cookie'] = COOKIE_UID + "; hm_token=" + self.token + "; Path=/; Domain=.global.hoymiles.com;" + \
            f"Expires=Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;" + "'"
        retv = self.send_payload(GET_ALL_DEVICE_API, header, payload)
        return retv['status'], retv['data']


    def send_payload(self, api, header, payload):
        retv = self.pega_url_jsonDic(BASE_URL + api, header, payload)
        if 'status' in retv.keys():
            if retv['status'] != "0":
                self.logger.debug(f"{api} Error: {retv['status']} {retv['message']}")
                if retv['status'] == "100":
                    # request new token
                    if (self.get_token()):
                        # chama pega solar novamente
                        retv['status'], retv['data'] = self.request_solar_data()
                elif retv['status'] == "3":
                    self.logger.error("Wrong plant id!!")
                    sys.exit(0)
        else:
            self.logger.error("I can't connect!")
        return retv


    def verify_plant(self):
        template = Template(PAYLOAD_ID)
        payload = template.substitute(id = self.plant_id)
        header = HEADER_DATA
        header['Cookie'] = COOKIE_UID + "; hm_token=" + self.token + "; Path=/; Domain=.global.hoymiles.com;" + \
            f"Expires=Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;" + "'"
        retv = self.send_payload(STATION_FIND, header, payload)
        if retv['status'] == '0':
            return True

        return False
     