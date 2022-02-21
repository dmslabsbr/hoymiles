import logging
import paho.mqtt.client as mqtt
import ssl
import time
from datetime import datetime
import json
import uuid
import socket

from const import MQTT_STATUS_CODE, MQTT_PUB
# from hoymiles import __version__


MQTTversion = mqtt.MQTTv31
TLS_protocol_version = ssl.PROTOCOL_TLSv1_2

module_logger = logging.getLogger('HoymilesAdd-on.mqttapi')

class MqttApi():

    def __init__(self, config) -> None:
        self._client = None
        self._config = config
        self.status = {}
        self.logger = logging.getLogger('HoymilesAdd-on.mqttapi.Mqtt')
        self.uuid = str(uuid.uuid1())
        self.last_mid = None
        self.client_status = False
        self.connected = False
        self.host_ip = self.get_ip()
        self.publicate_time = None

    def get_ip(self, change_dot = False, testIP = '192.168.1.1'):
        ''' Get device IP '''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect((testIP, 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '0.0.0.1'
        finally:
            s.close()
        if change_dot: IP=IP.replace('.','-')
        return str(IP)

    def start(self):
        ''' Start MQTT '''
        # MQTT Start
        # client = mqtt.Client(transport="tcp") # "websockets"
        self._client = mqtt.Client(client_id = '', clean_session = True, userdata = None, protocol = MQTTversion, transport="tcp" ) # mqtt.MQTTv31
        port = 1883
        user = self._config['MQTT_User']
        passw = self._config['MQTT_Pass']
        if self._config['MQTT_TLS']:
            port = self._config['MQTT_TLSPORT']

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

        #v.0.22 TLS
        if self._config['MQTT_TLS']:
            self.logger.info(f"Trying TLS: {self._config['MQTT_TLSPORT']}")
            self.logger.debug(f"TLS_protocol_version: {TLS_protocol_version}")
            context = ssl.SSLContext(protocol = TLS_protocol_version)
            self._client.tls_set_context(context)

        try:
            self.client_status = True
            #rc = client.connect(MQTT_HOST, MQTT_PORT, 60) # 1883
            rc = self._client.connect(host = self._config['MQTT_Host'],
                port = int(port),
                keepalive = 60)  # 1883

        except Exception as e:  # OSError
            if e.__class__.__name__ == 'OSError':
                self.client_status = False
                self.logger.warning("Can't start MQTT")
                self.logger.error("Can't start MQTT")
            else:
                self.client_status = False
        if self.client_status:  self._client.loop_start()  # start the loop


    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info(f"MQTT connected with result code {rc}")
        else:
            self.logger.error(f"MQTT connected with result code {rc}")

        if rc == 0:
            self.logger.info(f"Connected to {self._config['MQTT_Host']}")
            self.connected = True
            self.status["mqtt"] = "on"
            self._client.connected_flag = True
            # Mostra clientes
            self.status["ublish_time"] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            self.send_clients_status()
        else:
            self.status["mqtt"] = "off"
            if rc>5: rc=100
            #print (str(rc) + str(tp_c[rc]))
            self.logger.error(str(rc) + str(MQTT_STATUS_CODE[rc]))
            # tratar quando for 3 e outros
            if rc == 4 or rc == 5:
                # senha errada
                self.logger.error(f"APP EXIT {rc}")
                time.sleep(60000)
                #raise SystemExit(0)
                #sys.exit()
                #quit()

    def send_clients_status(self):
        ''' send connected clients status '''
        mqtt_topic = MQTT_PUB + "/clients/" + self.host_ip
        self.status['UUID'] = self.uuid
        self.status['version'] = 123
        #FIXME
        self.status['plant_id'] = 1234
        self.status['inHass'] = True
        jsonStatus = json.dumps(self.status)
        (rc, mid) = self.public(mqtt_topic, jsonStatus)
        return rc

    def public(self, topic, payload):
        "Publica no MQTT atual"
        (rc, mid) = self._client.publish(topic, payload)
        self.last_mid = mid
        if rc == mqtt.MQTT_ERR_NO_CONN:
            self.logger.debug("mqtt.MQTT_ERR_NO_CONN")
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self.last_mid = mid
        if rc == mqtt.MQTT_ERR_QUEUE_SIZE:
            self.logger.debug("mqtt.MQTT_ERR_QUEUE_SIZE")
        return rc, mid

    def on_publish(self, client, userdata, mid):
        # fazer o que aqui? 
        # fazer uma pilha para ver se foi publicado ou não
        # aparentemente só vem aqui, se foi publicado.
        if 1==2:
            print("Published mid: " + str(mid), "last: " + str(self.last_mid))
            if self.last_mid -1 != mid:
                self.logger.error(f"Error mid: {mid} no publiation.")


    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("disconnecting reason  "  + str(rc))
        if rc>5: rc=100
        print("disconnecting reason  "  + str(client) +  str(MQTT_STATUS_CODE[rc]))
        client.connected_flag = False
        client.disconnect_flag = True
        self.status.status['mqtt'] = "off"
        try:
            self.send_clients_status()
        except Exception as e:
            self.logger.warning("on_disconnect")