import hashlib
import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import date
from http.cookies import SimpleCookie
from urllib.parse import urlparse

import requests
from hoymiles.api_schema.data_count_station_real_data import DataCountStation
from hoymiles.cloud_payloads import Payload, TokenBody

try:
    from argon2.low_level import Type, hash_secret_raw

    ARGON2_AVAILABLE = True
except ImportError:
    Type = None
    hash_secret_raw = None
    ARGON2_AVAILABLE = False

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
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Minimal header for token/login requests (must match stable for compatibility)
HEADER_LOGIN = {"Content-Type": "application/json"}

BASE_URL = "https://neapi.hoymiles.com/"
VERSIONED_BASE_URL = "https://neapi.hoymiles.com/"
ESTAR_BASE_URL = "https://monitor.estarpower.com/platform/api/gateway/"

# Legacy gateway endpoints (used by fallback/older flows).
LEGACY_LOGIN_API = "iam/pub/0/auth/login"
LEGACY_GET_DATA_API = "pvm-data/api/0/station/data/count_station_real_data"

# Versioned API endpoints (aligned with stable/const.py semantics).
USER_ME_API_V = "iam/pub/{version}/user/user_me"
GET_DATA_API_V = "pvm-data/api/{version}/station/data/count_station_real_data"
GET_ALL_DEVICE_API_V = "pvm/api/{version}/station/select_device_of_tree"
STATION_FIND_API_V = "pvm/api/{version}/station/find"
DATA_FIND_DETAILS_API_V = "pvm/api/{version}/dev/micro/find"
SETTING_BATTERY_CONFIG_API_V = "pvm-ctl/api/{version}/dev/setting/write"

ARGON_PRE_INSP_API = "iam/pub/3/auth/pre-insp"
ARGON_LOGIN_API = "iam/pub/3/auth/login"


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


class CloudApi:
    cookies = None

    def __init__(self, config, tries=5) -> None:
        self.logger = logging.getLogger("HoymilesAdd-on.hoymilesapi.Hoymiles")

        self.connection = ConnectionHM()
        self._tries = tries
        self._config = config
        self.api_version = "0"
        self.token_method = "legacy"
        self.gateway_base_url = self._resolve_gateway_base_url()
        self.versioned_base_url = self._resolve_versioned_base_url()
        self.estar_mode = self._is_estar_mode()

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
        self,
        url: str,
        header: dict,
        payload: dict,
        include_auth: bool = True,
        include_cookies: bool = False,
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
        return self._send_request(
            url,
            header,
            payload,
            rtype="POST",
            include_auth=include_auth,
            include_cookies=include_cookies,
        )

    def send_options_request(
        self,
        url: str,
        header: dict,
        payload: dict,
        include_auth: bool = True,
        include_cookies: bool = False,
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
        return self._send_request(
            url,
            header,
            payload,
            rtype="OPTIONS",
            include_auth=include_auth,
            include_cookies=include_cookies,
        )

    def _send_request(
        self,
        url: str,
        header: dict,
        payload: dict,
        rtype: str,
        include_auth: bool = True,
        include_cookies: bool = False,
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
        # Always send JSON body for Hoymiles API calls.
        if is_dataclass(payload):
            payload = asdict(payload.body)

        if isinstance(payload, dict) or not isinstance(
            payload, (str, bytes, bytearray)
        ):
            payload = json.dumps(payload)

        header = dict(header)
        if include_auth and self.connection.token and "Authorization" not in header:
            header["Authorization"] = self.connection.token

        cookies_dict = {}
        if include_cookies and self.cookies:
            cookies_dict = {key: morsel.value for key, morsel in self.cookies.items()}

        sess = requests.Session()
        req = requests.Request(
            rtype, url, headers=header, data=payload, cookies=cookies_dict
        )
        prepped = req.prepare()
        self.logger.debug(prepped.headers)
        self.logger.debug(
            f"request body: {prepped.body}, header: {prepped.headers}, url: {prepped.url}, method: {prepped.method}, cookies: {prepped._cookies}"
        )

        try:
            response = sess.send(prepped)
            self.logger.debug(f"content: {response.content}")
            return response
        except Exception as err:
            self.logger.error(err)
            return None

    def _cfg_get(self, key: str, default=None):
        """Get config values from either dict-like or ConfigManager-like objects."""
        if isinstance(self._config, dict):
            return self._config.get(key, default)

        getter = getattr(self._config, "get", None)
        if callable(getter):
            try:
                return getter(key, default)
            except TypeError:
                value = getter(key)
                return default if value is None else value

        getter = getattr(self._config, "get_str", None)
        if callable(getter):
            value = getter(key, "")
            return default if value == "" else value

        return default

    def _normalize_base_url(self, value: str) -> str:
        value = (value or "").strip()
        if not value:
            return ""
        return value if value.endswith("/") else f"{value}/"

    def _is_estar_mode(self) -> bool:
        if self._cfg_get("USE_ESTAR", False):
            return True
        parsed = urlparse(self.gateway_base_url)
        return "estarpower" in (parsed.hostname or "")

    def _resolve_gateway_base_url(self) -> str:
        experimental = self._cfg_get("EXPERIMENTAL_CUSTOM_API_URLS", False)
        custom_gateway = self._normalize_base_url(
            self._cfg_get("API_GATEWAY_BASE_URL", "")
        )
        if experimental and custom_gateway:
            return custom_gateway
        if self._cfg_get("USE_ESTAR", False):
            return ESTAR_BASE_URL
        return BASE_URL

    def _resolve_versioned_base_url(self) -> str:
        experimental = self._cfg_get("EXPERIMENTAL_CUSTOM_API_URLS", False)
        custom_versioned = (self._cfg_get("API_VERSIONED_BASE_URL", "") or "").strip()
        if experimental and custom_versioned:
            return custom_versioned.rstrip("/")
        return VERSIONED_BASE_URL

    def _argon_compute_ch(self, password: str, a: str) -> str:
        """Compute Argon2 challenge hash used by modern S-Miles auth flow."""
        if not ARGON2_AVAILABLE:
            raise RuntimeError("argon2-cffi is not installed")

        salt = bytes.fromhex(a)
        raw = hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=3,
            memory_cost=32768,
            parallelism=1,
            hash_len=32,
            type=Type.ID,
        )
        return raw.hex()

    def _argon_get_token(self, user: str, password: str) -> tuple[bool, str]:
        """Get token using modern Argon2 login flow used by newer cloud versions."""
        pre_insp_payload = json.dumps({"u": user})
        pre_insp_resp = self.send_post_request(
            self.gateway_base_url + ARGON_PRE_INSP_API,
            dict(HEADER_LOGIN),
            pre_insp_payload,
            include_auth=False,
        )
        if not pre_insp_resp:
            return False, ""

        try:
            pre_insp_data = pre_insp_resp.json()
        except Exception:
            return False, ""

        if pre_insp_data.get("status") != "0":
            return False, ""

        insp_data = pre_insp_data.get("data", {})
        nonce = insp_data.get("n")
        salt = insp_data.get("a")
        if not nonce or not salt:
            return False, ""

        try:
            challenge = self._argon_compute_ch(password, salt)
        except Exception as err:
            self.logger.debug(f"Argon token computation failed: {err}")
            return False, ""

        login_payload = json.dumps({"u": user, "ch": challenge, "n": nonce})
        login_resp = self.send_post_request(
            self.gateway_base_url + ARGON_LOGIN_API,
            dict(HEADER_LOGIN),
            login_payload,
            include_auth=False,
        )
        if not login_resp:
            return False, ""

        try:
            login_data = login_resp.json()
        except Exception:
            return False, ""

        if login_data.get("status") != "0":
            return False, ""

        token = login_data.get("data", {}).get("token", "")
        return bool(token), token

    def _legacy_get_token(self, user: str, pass_hex: str) -> tuple[bool, str]:
        """Get token using legacy MD5-based login flow."""
        body = TokenBody(pass_hex, user)
        payload = Payload(body)

        resp = self.send_post_request(
            self.gateway_base_url + LEGACY_LOGIN_API,
            HEADER_LOGIN,
            payload,
            include_auth=False,
        )
        if not resp:
            return False, ""

        try:
            data = resp.json()
        except Exception:
            return False, ""

        if data.get("status") != "0":
            return False, ""

        token = data.get("data", {}).get("token") or data.get("data", {}).get(
            "estar_token", ""
        )
        return bool(token), token

    def _versioned_api_url(self, path_template: str) -> str:
        """Build neapi URL using the currently selected cloud API version."""
        return (
            f"{self.versioned_base_url}{path_template.format(version=self.api_version)}"
        )

    def _post_with_auth_retry(self, url: str, payload: dict) -> requests.Response:
        """POST with auth token and one retry on token-expired status."""
        resp = self.send_post_request(url, HEADER_DATA, payload)
        if not resp:
            return resp

        try:
            data = resp.json()
        except Exception:
            return resp

        if isinstance(data, dict) and data.get("status") == "100" and self.get_token():
            return self.send_post_request(url, HEADER_DATA, payload)

        return resp

    def _apply_debug_forced_api_version(self) -> None:
        """Override auto-selected API version when debug forcing is enabled."""
        if not self._cfg_get("DEBUG_FORCE_API_VERSION", False):
            return

        forced = str(self._cfg_get("DEBUG_API_VERSION", "")).strip()
        if forced not in {"0", "3"}:
            self.logger.warning(
                "DEBUG_FORCE_API_VERSION is enabled but DEBUG_API_VERSION=%r is invalid",
                forced,
            )
            return

        if forced != self.api_version:
            self.logger.warning(
                "Forcing API version /%s/ for debug (auto-selected was /%s/)",
                forced,
                self.api_version,
            )
        self.api_version = forced

    def get_token(self) -> bool:
        """Get token from Hoymiles API

        :return: True if token was obtained, False otherwise
        :rtype: bool
        """
        user = self._cfg_get("HOYMILES_USER", "")
        password = self._cfg_get("HOYMILES_PASSWORD", "")
        if not user or not password:
            self.logger.error("Missing HOYMILES_USER or HOYMILES_PASSWORD")
            return False

        pass_hash = hashlib.md5(password.encode())
        pass_hex = pass_hash.hexdigest()

        # Newer cloud versions require Argon2 challenge flow, while legacy
        # servers still accept MD5 login. Try modern first, then fallback.
        status, token = self._argon_get_token(user, password)
        if not status:
            status, token = self._legacy_get_token(user, pass_hex)
            if status:
                self.api_version = "0"
                self.token_method = "legacy"
        else:
            self.api_version = "3"
            self.token_method = "argon"

        if not status or not token:
            self.logger.error("Error in login using both token methods")
            return False

        self._apply_debug_forced_api_version()

        self.logger.info(
            "Token acquired via %s method; using /%s/ API endpoints",
            self.token_method,
            self.api_version,
        )

        self.connection.token = token
        return True

    def init_cookies(self):
        """Basic cookie initialization"""
        self.cookies = SimpleCookie()
        self.cookies.load(
            "uid=fff9c382-389f-4a47-8dc9-c5486fc3d9f5;EGG_SESS=XHfAhiHWwU__OUVeKh0IiITBnmwA-IIXEzTCHgHgww6ZYYddOPntPSwVz4Gx7ISbfU0WrvzOLungThcL-9D2KxavrtyPk8Mr2YXLFzJwvM0usPvhzYdt2Y2S9Akt5sjP;Path=/;"
        )

    def upate_cookie(self):
        """Update cookie with token and proper domain"""
        cookie_domain = (self._cfg_get("API_COOKIE_DOMAIN", "") or "").strip()
        if not cookie_domain:
            host = urlparse(self.gateway_base_url).hostname or "global.hoymiles.com"
            cookie_domain = f".{host}"

        if self.estar_mode:
            self.cookies["estar_token"] = self.connection.token
            self.cookies["estar_token_language"] = "en_us"
            self.cookies["estar_token"]["Expires"] = (
                f"Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;"
            )
            self.cookies["estar_token"]["Domain"] = cookie_domain
        else:
            self.cookies["hm_token"] = self.connection.token
            self.cookies["hm_token_language"] = "en_us"
            self.cookies["hm_token"]["Expires"] = (
                f"Sat, 30 Mar {date.today().year + 1} 22:11:48 GMT;"
            )
            self.cookies["hm_token"]["Domain"] = cookie_domain

    def get_credentials(self) -> tuple[str, str]:
        """Get credentials for Hoymiles API from config

        :return: Tuple with user and password hash
        :rtype: Tuple[str, str]
        """
        user = self._cfg_get("HOYMILES_USER", "")
        pass_hash = hashlib.md5(self._cfg_get("HOYMILES_PASSWORD", "").encode())
        pass_hex = pass_hash.hexdigest()
        return user, pass_hex

    def request_solar_data(self, plant_id: str) -> requests.Response:
        """Request solar data from Hoymiles API

        :param plant_id: ID of the plant
        :type plant_id: str
        :return: Response from API
        :rtype: requests.Response
        """

        payload = {"sid": plant_id}

        if self.estar_mode and not self._cfg_get("EXPERIMENTAL_CUSTOM_API_URLS", False):
            # Keep old endpoint for ESTAR compatibility.
            return self._post_with_auth_retry(
                self.gateway_base_url + LEGACY_GET_DATA_API,
                payload,
            )

        return self._post_with_auth_retry(
            self._versioned_api_url(GET_DATA_API_V),
            payload,
        )

    def request_plant_hw(self, plant_id: str) -> requests.Response:
        """Request hardware/device tree for a plant."""
        payload = {"id": plant_id}
        return self._post_with_auth_retry(
            self._versioned_api_url(GET_ALL_DEVICE_API_V),
            payload,
        )

    def get_plant_hw(self, plant_id: str) -> list[dict]:
        """Get parsed hardware/device tree list for a plant."""
        if not self.connection.token and not self.get_token():
            self.logger.error("Unable to fetch token before hardware request")
            return []

        resp = self.request_plant_hw(plant_id)
        if not resp:
            return []

        try:
            data = resp.json()
        except Exception:
            return []

        if data.get("status") != "0":
            return []

        return data.get("data", [])

    def verify_plant(self, plant_id: str) -> bool:
        """Verify that current user has access to plant id."""
        if not self.connection.token and not self.get_token():
            self.logger.error("Unable to fetch token before plant verification")
            return False

        resp = self._post_with_auth_retry(
            self._versioned_api_url(STATION_FIND_API_V),
            {"id": plant_id},
        )
        if not resp:
            return False

        try:
            data = resp.json()
        except Exception:
            return False

        return data.get("status") == "0"

    def request_micro_details(self, micro_id: str | int) -> requests.Response:
        """Request micro-inverter details/alarm info."""
        return self._post_with_auth_retry(
            self._versioned_api_url(DATA_FIND_DETAILS_API_V),
            {"id": micro_id},
        )

    def set_bms_mode(
        self, plant_id: str, mode: int, reserve_soc: int, max_power: int = 0
    ) -> bool:
        """Set battery mode configuration."""
        payload = {
            "mode": mode,
            "data": {"reserve_soc": reserve_soc},
            "sid": plant_id,
        }
        if max_power:
            payload["data"]["max_power"] = max_power

        resp = self._post_with_auth_retry(
            self._versioned_api_url(SETTING_BATTERY_CONFIG_API_V),
            payload,
        )
        if not resp:
            return False

        try:
            data = resp.json()
        except Exception:
            return False

        return data.get("status") == "0"

    def get_solar_data(self, plant_id: str) -> dict:
        """Get solar data from Hoymiles API

        :param plant_id: ID of the plant
        :type plant_id: str
        :return: Solar data
        :rtype: dict
        """
        if not self.connection.token and not self.get_token():
            self.logger.error("Unable to fetch token before data request")
            return {}

        resp = self.request_solar_data(plant_id)
        if not resp:
            return {}

        data = resp.json()

        # Token expired; refresh once and retry.
        if data.get("status") == "100" and self.get_token():
            resp = self.request_solar_data(plant_id)
            if not resp:
                return {}
            data = resp.json()

        if data.get("status") == "1":
            self.logger.error(
                f"Error in get data : {resp.status_code} {HTTP_STATUS_CODE.get(resp.status_code, 1000)}"
            )
            return {}

        # Validate response against schema for type safety
        try:
            response = DataCountStation.model_validate(data)
            return response.data.model_dump()
        except (ValueError, TypeError) as err:
            self.logger.warning(
                f"Solar data schema validation failed: {err}; returning raw data"
            )
            return data.get("data", {})
