"""
API for mqtt communication
"""

import json
import logging
import socket
import ssl
import time
import uuid
from datetime import datetime

import paho.mqtt.client as mqtt

from const import MQTT_PUB, MQTT_STATUS_CODE
from hoymilesapi import Hoymiles

MQTT_VERSION = mqtt.MQTTv31
TLS_PROTOCOL_VERSION = ssl.PROTOCOL_TLSv1_2

module_logger = logging.getLogger("HoymilesAdd-on.mqttapi")


class MqttApi:
    """Mqtt API main calass"""

    def __init__(self, config: dict, plant_id: str, version) -> None:
        self._client = None
        self._config = config
        self.logger = logging.getLogger("HoymilesAdd-on.mqttapi.Mqtt")
        self.uuid = str(uuid.uuid1())
        self.last_mid = None
        self.client_status = False
        self.connected = False
        self.host_ip = self.get_ip()
        self.publicate_time = None

        self.status = {}
        self.status["UUID"] = self.uuid
        self.status["version"] = version
        self.status["plant_id"] = plant_id
        self.status["inHass"] = True

        self._client = mqtt.Client(
            client_id=self.uuid,
            clean_session=True,
            userdata=None,
            protocol=MQTT_VERSION,
            transport="tcp",
        )  # mqtt.MQTTv31

    def get_ip(self, change_dot=False, test_ip="192.168.1.1"):
        """Get device IP"""
        soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            soc.connect((test_ip, 1))
            self_ip = soc.getsockname()[0]
        except Exception:
            self_ip = "0.0.0.1"
        finally:
            soc.close()
        if change_dot:
            self_ip = self_ip.replace(".", "-")
        return str(self_ip)

    def start(self):
        """Start MQTT"""
        # MQTT Start
        # client = mqtt.Client(transport="tcp") # "websockets"
        self.logger.info(f"mqtt.Client {self.uuid}")

        if not self._client.is_connected():
            port = 1883
            user = self._config["MQTT_User"]
            passw = self._config["MQTT_Pass"]
            if self._config["MQTT_TLS"]:
                port = self._config["MQTT_TLS_PORT"]

            self.logger.info(f"Starting MQTT {self._config['MQTT_Host']}")
            self.logger.debug(f"SSL: {ssl.OPENSSL_VERSION}")
            self.logger.debug(f"mqttStart TLS: {self._config['MQTT_TLS']}")
            self.logger.debug(f"mqttStart MQTT_USERNAME: {user}")
            self.logger.debug(f"mqttStart MQTT_PASSWORD: {passw}")
            self.logger.debug(f"mqttStart MQTT_PORT: {port}")

            self._client.username_pw_set(username=user, password=passw)
            self._client.on_connect = self.on_connect
            self._client.on_disconnect = self.on_disconnect
            self._client.on_publish = self.on_publish

            # v.0.22 TLS
            if self._config["MQTT_TLS"]:
                self.logger.info(f"Trying TLS: {self._config['MQTT_TLS_PORT']}")
                self.logger.debug(f"TLS_protocol_version: {TLS_PROTOCOL_VERSION}")
                context = ssl.SSLContext(protocol=TLS_PROTOCOL_VERSION)
                self._client.tls_set_context(context)

            try:
                self.client_status = True
                # rc = client.connect(MQTT_HOST, MQTT_PORT, 60) # 1883
                self._client.connect(
                    host=self._config["MQTT_Host"], port=int(port), keepalive=60
                )  # 1883

            except Exception as err:  # OSError
                if err.__class__.__name__ == "OSError":
                    self.client_status = False
                    self.logger.error("Can't start MQTT")
                else:
                    self.client_status = False
                    self.logger.error(f"{err}")
            if self.client_status:
                self._client.loop_start()  # start the loop

    def on_connect(
        self, client, userdata, flags, ret_code
    ):  # pylint: disable=unused-argument
        """Mqtt on connect

        Args:
            client (_type_): _description_
            userdata (_type_): _description_
            flags (_type_): _description_
            ret_code (_type_): _description_
        """
        if ret_code == 0:
            self.logger.info(f"MQTT connected with result code {ret_code}")
        else:
            self.logger.error(f"MQTT connected with result code {ret_code}")

        if ret_code == 0:
            self.logger.info(f"Connected to {self._config['MQTT_Host']}")
            self.connected = True
            self.status["mqtt"] = "on"
            self._client.connected_flag = True
            # Mostra clientes
            self.status["ublish_time"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            self.send_clients_status()
        else:
            self.status["mqtt"] = "off"
            if ret_code > 5:
                ret_code = 100
            # print (str(rc) + str(tp_c[rc]))
            self.logger.error(f"{ret_code} {MQTT_STATUS_CODE[ret_code]}")
            # tratar quando for 3 e outros
            if ret_code in (4, 5):
                # senha errada
                self.logger.error(f"APP EXIT {ret_code}")
                time.sleep(60000)
                # raise SystemExit(0)
                # sys.exit()
                # quit()

    def send_clients_status(self):
        """send connected clients status"""
        mqtt_topic = MQTT_PUB + "/clients/" + self.host_ip
        json_status = json.dumps(self.status)
        return self.public(mqtt_topic, json_status)

    def public(self, topic, payload):
        "Publica no MQTT atual"
        ret_code, mid = self._client.publish(topic, payload)
        self.last_mid = mid
        if ret_code == mqtt.MQTT_ERR_NO_CONN:
            self.logger.debug("mqtt.MQTT_ERR_NO_CONN")
        if ret_code == mqtt.MQTT_ERR_SUCCESS:
            self.last_mid = mid
        if ret_code == mqtt.MQTT_ERR_QUEUE_SIZE:
            self.logger.debug("mqtt.MQTT_ERR_QUEUE_SIZE")
        return ret_code

    def on_publish(self, client, userdata, mid):  # pylint: disable=unused-argument
        """Mqtt on publish

        Args:
            client (_type_): _description_
            userdata (_type_): _description_
            mid (_type_): _description_
        """
        # fazer o que aqui?
        # fazer uma pilha para ver se foi publicado ou não
        # aparentemente só vem aqui, se foi publicado.
        if 1 == 2:
            print("Published mid: " + str(mid), "last: " + str(self.last_mid))
            if self.last_mid - 1 != mid:
                self.logger.error(f"Error mid: {mid} no publiation.")

    def on_disconnect(
        self, client, userdata, ret_code
    ):  # pylint: disable=unused-argument
        """Mqtt on disconnect

        Args:
            client (_type_): _description_
            userdata (_type_): _description_
            ret_code (_type_): _description_
        """
        self.connected = False
        print("disconnecting reason  " + str(ret_code))
        if ret_code > 5:
            ret_code = 100
        print("disconnecting reason  " + str(client) + str(MQTT_STATUS_CODE[ret_code]))
        client.connected_flag = False
        client.disconnect_flag = True
        self.status["mqtt"] = "off"
        try:
            self.send_clients_status()
        except Exception as err:
            self.logger.warning(f"on_disconnect {err}")
