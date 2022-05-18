"""
Main API for Hoymiles
"""

import hashlib
import json
import logging
from pyexpat.errors import messages
import re
import sys
import time
import uuid
from datetime import date, datetime
from string import Template

import requests

from const import (BASE_URL, COOKIE_EGG_SESS, COOKIE_UID, GET_ALL_DEVICE_API,
                   GET_DATA_API, HEADER_DATA, HEADER_LOGIN, HTTP_STATUS_CODE,
                   LOCAL_TIMEZONE, LOGIN_API, PAYLOAD_ID, PAYLOAD_T1,
                   PAYLOAD_T2, STATION_FIND, PAYLOAD_DETAILS, DATA_FIND_DETAILS)

module_logger = logging.getLogger('HoymilesAdd-on.hoymilesapi')


class PlantObject():
    """Generic class for devices in plant
    """
    data = {'connect': ''
            }

    def __init__(self, data: dict) -> None:
        self.id = data['id']  # pylint: disable=invalid-name
        self.sn = data['sn']  # pylint: disable=invalid-name
        self.soft_ver = data['soft_ver']
        self.hard_ver = data['hard_ver']
        if data['warn_data']['connect']:
            self.data['connect'] = "ON"
        else:
            self.data['connect'] = "ON"
        self.uuid = str(uuid.uuid1())
        self.err_code = 0
        self.err_msg = ""


class Dtu(PlantObject):
    """Class representig DTU device
    """

    def __init__(self, dtu_data: dict) -> None:
        super(Dtu, self).__init__(dtu_data)
        self.model_no = dtu_data['model_no']


class Micros(PlantObject):
    """Class representig Microinverter device
    """
    data = {'connect': '',
            'alarm_code': 0,
            'alarm_string': ''
            }
    def __init__(self, micro_data: dict) -> None:
        super(Micros, self).__init__(micro_data)
        self.init_hard_no = micro_data['init_hard_no']


class Hoymiles(object):
    """Class for getting data from S-Miles Cloud
    """

    data_dict = {"last_time": "", "load_time": "",
                 'load_cnt': 0}

    def __init__(self, plant_id, config, g_envios, tries=5) -> None:
        self.plant_id = plant_id
        self.token = None
        self._tries = tries
        self.logger = logging.getLogger('HoymilesAdd-on.hoymilesapi.Hoymiles')
        self.count_station_real_data = {}
        self._config = config
        self.g_envios = g_envios
        self.solar_data = {}
        self.load_cnt = 0
        self.dtu_list = []
        self.micro_list = []
        self.uuid = str(uuid.uuid1())

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

    def get_token(self) -> bool:
        """Getter for token

        Returns:
            bool: Status of getting token operation
        """
        user = self._config['HOYMILES_USER']
        pass_hash = hashlib.md5(
            self._config['HOYMILES_PASSWORD'].encode())  # b'senhadohoymiles'
        pass_hex = pass_hash.hexdigest()

        ret = False
        template = Template(PAYLOAD_T1)
        payload = template.substitute(user=user, password=pass_hex)
        header = HEADER_LOGIN
        header['Cookie'] = COOKIE_UID + "; " + COOKIE_EGG_SESS
        login, s_code = self.send_post_request(
            BASE_URL + LOGIN_API, header, payload)
        if s_code == 200:
            json_res = json.loads(login)
            if json_res['status'] == '0':
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
            self.logger.error(
                f'Wrong user/password {s_code} {HTTP_STATUS_CODE.get(s_code, 1000)}')
        return ret

    def send_post_request(self, url: str, header: dict, payload: str):
        """Send post API request

        Args:
            url (str): Full API url
            header (dict): message header
            payload (str): payload

        Returns:
            _type_: _description_s
        """
        return self.send_request(url, header, payload, rtype='POST')

    def send_options_request(self, url: str, header: dict, payload: str):
        """Send options API request

        Args:
            url (str): Full API url
            header (dict): message header
            payload (str): payload

        Returns:
            _type_: _description_
        """
        return self.send_request(url, header, payload, rtype='OPTIONS')

    def send_request(self, url: str, header: dict, payload: str, rtype: str):
        """_summary_

        Args:
            url (str): Full API url
            header (dict): message header
            payload (str): payload
            rtype (str): Request type

        Returns:
            _type_: _description_
        """
        self.logger.info(f"Loading: {url}")
        sess = requests.Session()
        req = requests.Request(rtype, url, headers=header,
                               data=payload.replace('\n', "").encode('utf-8'))
        sess = requests.Session()
        prepped = req.prepare()
        self.logger.debug(prepped.headers)
        try:
            response = sess.send(prepped)
            ret = ""
            if response.status_code != 200:
                self.logger.error(f"Access error: {url}")
                self.logger.error(
                    f"Status code: {response.status_code}" +
                    f"{HTTP_STATUS_CODE.get(response.status_code, 1000)}")
            else:
                ret = response.content
                self.logger.debug(f"content: {response.content}")
            return ret, response.status_code
        except Exception as err:
            self.logger.error(err)
            return "", -1

    def get_solar_data(self) -> dict:
        """Get solar data

        Returns:
            dict: data returned by API
        """
        status, self.solar_data = self.request_solar_data()
        if status == 0:
            self.data_dict['load_time'] = datetime.today().strftime(
                '%Y-%m-%d %H:%M:%S')
            self.data_dict['load_cnt'] += 1

            self.logger.debug(f"solar_data: {self.solar_data}")
            if not self.solar_data['real_power']:
                self.logger.warning("REAL_POWER = 0")
                time.sleep(60)  # espera 60 segundos
                self.logger.info("Getting data again")
                status, self.solar_data = self.request_solar_data()

            capacity = float(self.solar_data['capacitor'])

            if capacity == 0:
                self.logger.error(f"Error capacitor: {capacity}")
            else:
                self.solar_data = self.adjust_solar_data(self.solar_data)
        return self.solar_data

    def adjust_solar_data(self, solar_data: dict) -> dict:
        """Adjust solar data like unifed measurements units

        Args:
            solar_data (dict): data retrun from API

        Returns:
            dict: adjusted solar data
        """
        real_power = float(solar_data['real_power'])
        capacidade = float(solar_data['capacitor'])
        if 0 < capacidade < 100:
            capacidade = capacidade * 1000
        power_ratio = (real_power / capacidade) * 100
        power_ratio = round(power_ratio, 1)
        if real_power == 0:
            self.logger.warning("real_power = 0")

        solar_data['real_power'] = str(real_power)
        solar_data['real_power_kw'] = str(round(real_power/1000, 3))
        solar_data['real_power_measurement'] = str(real_power)
        solar_data['real_power_total_increasing'] = str(real_power)
        solar_data['power_ratio'] = str(power_ratio)
        solar_data['capacitor'] = str(capacidade)
        solar_data['capacitor_kW'] = str(capacidade / 1000)
        co2 = round(float(solar_data['co2_emission_reduction']) / 1000000, 5)
        solar_data['co2_emission_reduction'] = str(co2)
        solar_data['today_eq_Wh'] = solar_data['today_eq']
        solar_data['today_eq'] = str(
            round(float(solar_data['today_eq']) / 1000, 2))
        solar_data['month_eq'] = str(
            round(float(solar_data['month_eq']) / 1000, 2))
        solar_data['year_eq'] = str(
            round(float(solar_data['year_eq']) / 1000, 2))
        solar_data['total_eq'] = str(
            round(float(solar_data['total_eq']) / 1000, 2))

        last_data_time = solar_data['last_data_time']
        last_data_time = datetime.strptime(last_data_time, '%Y-%m-%d %H:%M:%S')
        solar_data['last_data_time'] = last_data_time.replace(
            tzinfo=LOCAL_TIMEZONE).isoformat()
        self.logger.info(f"last_data_time {solar_data['last_data_time']}")

        return solar_data

    def request_solar_data(self):
        """Send request for solar data

        Returns:
            _type_: _description_
        """
        template = Template(PAYLOAD_T2)
        payload = template.substitute(sid=self.plant_id)

        header = HEADER_DATA
        header['Cookie'] = COOKIE_UID + "; hm_token=" + self.token + \
            "; Path=/; Domain=.global.hoymiles.com;" + \
            f"Expires=Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;" + "'"

        solar = self.send_payload(GET_DATA_API, header, payload)
        return int(solar['status']), solar['data']

    def get_plant_hw(self):
        """Get pland hardware layout and create objects
        """
        status, hws_data = self.request_plant_hw()
        if int(status) == 0:
            for hw_data in hws_data:
                try:
                    dtu_data = hw_data['dtu']
                    self.dtu_list.append(Dtu(dtu_data))
                except Exception as err:
                    self.logger.error(f"request_plant_hw dtu {err}")

                if 'micros' in hw_data['repeater_list'][0].keys():
                    for micro in hw_data['repeater_list'][0]['micros']:
                        self.micro_list.append(Micros(micro))

    def update_devices_status(self):
        """Update status of all plant devices
        """
        status, hws_data = self.request_plant_hw()
        if status == 0:
            for hw_data in hws_data:
                for dtu in self.dtu_list:
                    try:
                        if hw_data['dtu']['sn'] == dtu.sn:
                            if hw_data['dtu']['warn_data']['connect']:
                                dtu.data['connect'] = "ON"
                            else:
                                dtu.data['connect'] = "OFF"
                    except Exception as err:
                        self.logger.error(f"request_plant_hw dtu {err}")

                try:
                    if 'micros' in hw_data['repeater_list'][0].keys():
                        for micro in hw_data['repeater_list'][0]['micros']:
                            for device in self.micro_list:
                                if micro['sn'] == device.sn:
                                    if micro['warn_data']['connect']:
                                        device.data['connect'] = "ON"
                                    else:
                                        device.data['connect'] = "OFF"
                except Exception as err:
                    self.logger.warning(f"Faild updating {err}")
                    self.logger.warning("Dump data for analysis")
                    self.logger.warning(f"{hws_data}")

    def request_plant_hw(self):
        """Send request for getting hardware plant list.

        Returns:
            _type_: _description_
        """
        template = Template(PAYLOAD_ID)
        payload = template.substitute(id=self.plant_id)
        header = HEADER_DATA
        header['Cookie'] = COOKIE_UID + "; hm_token=" + self.token + \
            "; Path=/; Domain=.global.hoymiles.com;" + \
            f"Expires=Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;" + "'"
        retv = self.send_payload(GET_ALL_DEVICE_API, header, payload)
        return retv['status'], retv['data']

    def send_payload(self, api: str, header: dict, payload: str) -> dict:
        """Send api payload

        Args:
            api (str): part of api adress
            header (dict): message header
            payload (str): payload

        Returns:
            dict: _description_
        """
        # retv = self.pega_url_json_dic(BASE_URL + api, header, payload)
        retv, s_code = self.send_request(
            BASE_URL + api, header, payload, 'POST')
        retv = json.loads(retv)
        if s_code == 200:
            if 'status' in retv.keys():
                if retv['status'] != "0":
                    self.logger.debug(
                        f"{api} Error: {retv['status']} {retv['message']}")
                    if retv['status'] == "100":
                        # request new token
                        if self.get_token():
                            # chama pega solar novamente
                            retv['status'], retv['data'] = self.request_solar_data()
                    elif retv['status'] == "3":
                        self.logger.error("Wrong plant id!!")
                        sys.exit(0)
            else:
                self.logger.error("I can't connect!")
        return retv

    def verify_plant(self) -> bool:
        """Verify id user has access to plant

        Returns:
            bool: True/False
        """
        template = Template(PAYLOAD_ID)
        payload = template.substitute(id=self.plant_id)
        header = HEADER_DATA
        header['Cookie'] = COOKIE_UID + "; hm_token=" + self.token + \
            "; Path=/; Domain=.global.hoymiles.com;" + \
            f"Expires=Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;" + "'"
        retv = self.send_payload(STATION_FIND, header, payload)
        if retv['status'] == '0':
            return True

        return False

    def get_alarms(self):
        """_summary_
        """
        header = HEADER_DATA
        header['Cookie'] = COOKIE_UID + "; hm_token=" + self.token + \
            "; Path=/; Domain=.global.hoymiles.com;" + \
            f"Expires=Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;" + "'"
        for micro in self.micro_list:
            template = Template(PAYLOAD_DETAILS)
            payload = template.substitute(
                mi_id=micro.id, mi_sn=micro.sn, sid=self.plant_id,
                time=datetime.now().strftime('%Y-%m-%d %H:%M'))
            retv = self.send_payload(DATA_FIND_DETAILS, header, payload)
            try:
                if retv["data"]["warn_list"]:
                    micro.data['alarm_code'] = int(retv["data"]["warn_list"][0]["err_code"])
                    micro.data['alarm_string'] = self.get_alarm_description(micro.err_code)
                    micro.data['alarm_string'] += " " + retv["data"]["warn_list"][0]["wd1"]
                    micro.data['alarm_string'] += " " + retv["data"]["warn_list"][0]["wdd2"]
                    micro.data['alarm_string'] += " " + retv["data"]["warn_list"][0]["wd2"]
                else:
                    micro.data['alarm_code'] = 0
                    micro.data['alarm_string'] = ""
            except Exception as err:
                self.logger.warning(f"{err}")

    def get_alarm_description(self, code: int) -> str:
        """Getting alarm description based on id

        Args:
            code (int): error code

        Returns:
            str: error description
        """
        try:
            with open("jsons/micro_codes", 'r', encoding="utf-8") as infile:
                for line in infile:
                    error_set = line.split(':')
                    if str(code) in error_set[-1]:
                        return error_set[0]
        except Exception as err:
            self.logger.warning(
                f"There was a problem while opening error list {err}")
        return ""
