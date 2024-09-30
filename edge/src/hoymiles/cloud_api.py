import hashlib
import logging
from pyexpat.errors import messages
from datetime import date, datetime
from typing import Tuple
from http.cookies import SimpleCookie

from hoymiles.cloud_payloads import TokenBody, Payload, SidBody
from dataclasses import asdict

import requests

module_logger = logging.getLogger("HoymilesAdd-on.hoymilesapi")


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

HEADER_DATA = {
    "Content-Type": "application/json;charset=UTF-8",
    "Cache-Control": "no-cache",
    "Host": "global.hoymiles.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",  # pylint: disable=line-too-long
    "Accept-Language": "pt-BR,pt;q=0.9,it-IT;q=0.8,it;q=0.7,es-ES;q=0.6,es;q=0.5,en-US;q=0.4,en;q=0.3",  # pylint: disable=line-too-long
}

BASE_URL = "https://global.hoymiles.com/platform/api/gateway/"
LOGIN_API = "iam/auth_login"
USER_ME = "iam/user_me"
GET_DATA_API = "pvm-data/data_count_station_real_data"
GET_ALL_DEVICE_API = "pvm/station_select_device_of_tree"
STATION_FIND = "pvm/station_find"
DATA_FIND_DETAILS = "pvm-data/data_find_details"
SETTING_BATTERY_CONFIG = "pvm/setting_battery_config"


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class ConnectionHM(metaclass=SingletonMeta):
    token = None


class CloudApi(object):
    cookies = None

    def __init__(self, config, tries=5) -> None:
        self.logger = logging.getLogger("HoymilesAdd-on.hoymilesapi.Hoymiles")

        self.connection = ConnectionHM()
        self._tries = tries
        self._config = config

        self.init_cookies()

        # cnt = 0
        # while True:
        #     if not self.get_token():
        #         self.logger.error("I can't get access token - sleeping 300s")
        #         if cnt >= self._tries:
        #             exit()
        #         time.sleep(300)
        #         cnt += 1
        #     else:
        #         break

    def send_post_request(
        self, url: str, header: dict, payload: dict
    ) -> requests.Response:
        """Send POST request to Hoymiles API

        :param url: Full API url
        :type url: str
        :param header: message header
        :type header: dict
        :param payload: message payload
        :type payload: dict
        :return: Response from API otherwise None
        :rtype: requests.Response
        """
        return self._send_request(url, header, payload, rtype="POST")

    def send_options_request(
        self, url: str, header: dict, payload: dict
    ) -> requests.Response:
        """Send OPTIONS request to Hoymiles API

        :param url: Full API url
        :type url: str
        :param header: message header
        :type header: dict
        :param payload: message payload
        :type payload: dict
        :return: Response from API otherwise None
        :rtype: requests.Response
        """
        return self._send_request(url, header, payload, rtype="OPTIONS")

    def _send_request(
        self, url: str, header: dict, payload: dict, rtype: str
    ) -> requests.Response:
        """Send API request

        :param url: Full API url
        :type url: str
        :param header: message header
        :type header: dict
        :param payload: message payload
        :type payload: dict
        :param rtype: Request type (GET, POST, PUT, DELETE)
        :type rtype: str
        :return: Response from API otherwise None
        :rtype: requests.Response
        """
        self.logger.info(f"Loading: {url}")
        self.logger.debug(f"payload: {payload}")

        sess = requests.Session()
        req = requests.Request(
            rtype, url, headers=header, data=payload, cookies=self.cookies
        )
        prepped = req.prepare()
        self.logger.debug(prepped.headers)
        try:
            response = sess.send(prepped)
            self.logger.debug(f"content: {response.content}")
            return response
        except Exception as err:
            self.logger.error(err)
            return None

    def get_token(self) -> bool:
        """Get token from Hoymiles API

        :return: True if token was obtained, False otherwise
        :rtype: bool
        """
        user, pass_hex = self.get_credentials()

        body = TokenBody(pass_hex, user)
        payload = Payload(body)

        resp = self.send_post_request(BASE_URL + LOGIN_API, HEADER_DATA, payload)

        if not resp or resp.json().get("status") != "0":
            self.logger.error(
                f"Error in login : {resp.status_code} {HTTP_STATUS_CODE.get(resp.status_code, 1000)}"
            )
            return False

        self.connection.token = resp.json().get("data").get("token")
        if not resp.json().get("data").get("token"):
            if not resp.json().get("data").get("estar_token"):
                self.logger.error("No response")
                return False
            self.connection.token = resp.json().get("data").get("estar_token")

        self.upate_cookie()
        return True

    def init_cookies(self):
        """Basic cookie initialization"""
        self.cookies = SimpleCookie()
        self.cookies.load(
            "uid=fff9c382-389f-4a47-8dc9-c5486fc3d9f5;EGG_SESS=XHfAhiHWwU__OUVeKh0IiITBnmwA-IIXEzTCHgHgww6ZYYddOPntPSwVz4Gx7ISbfU0WrvzOLungThcL-9D2KxavrtyPk8Mr2YXLFzJwvM0usPvhzYdt2Y2S9Akt5sjP;Path=/;"
        )

    def upate_cookie(self):
        """Update cookie with token and proper domain"""
        if self._config.get("USE_ESTAR", False):
            self.cookies["estar_token"] = self.connection.token
            self.cookies["estar_token_language"] = "en_us"
            self.cookies["estar_token"][
                "Expires"
            ] = f"Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;"
            self.cookies["estar_token"]["Domain"] = ".monitor.estarpower.com"
        else:
            self.cookies["hm_token"] = self.connection.token
            self.cookies["hm_token_language"] = "en_us"
            self.cookies["hm_token"][
                "Expires"
            ] = f"Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;"
            self.cookies["hm_token"]["Domain"] = ".global.hoymiles.com"

    def get_credentials(self) -> Tuple[str, str]:
        """Get credentials for Hoymiles API from config

        :return: Tuple with user and password hash
        :rtype: Tuple[str, str]
        """
        user = self._config["HOYMILES_USER"]
        pass_hash = hashlib.md5(self._config["HOYMILES_PASSWORD"].encode())
        pass_hex = pass_hash.hexdigest()
        return user, pass_hex

    def request_solar_data(self, plant_id: str) -> requests.Response:
        """Request solar data from Hoymiles API

        :param plant_id: ID of the plant
        :type plant_id: str
        :return: Response from API
        :rtype: requests.Response
        """

        body = SidBody(plant_id)
        payload = Payload(body)
        return self.send_post_request(BASE_URL + GET_DATA_API, HEADER_DATA, payload)

    def get_solar_data(self, plant_id: str) -> dict:
        """Get solar data from Hoymiles API

        :param plant_id: ID of the plant
        :type plant_id: str
        :return: Solar data
        :rtype: dict
        """
        resp = self.request_solar_data(plant_id)
        if not resp or resp.json().get("status") == "1":
            self.logger.error(
                f"Error in get data : {resp.status_code} {HTTP_STATUS_CODE.get(resp.status_code, 1000)}"
            )
            return {}

        return resp.json().get("data", {})
