__author__ = 'dmslabs&Cosik'
__version__ = '0.24.2d'
__app_name__ = 'Hoymiles Gateway'

import logging
import os
import sys
from datetime import datetime, timedelta
from configparser import ConfigParser
import time
import json
from string import Template


from const import SECRETS, SHORT_NAME, SID, json_hass, MQTT_HASS, device_dict, EXPIRE_TIME, NODE_ID, MQTT_PUB, HASS_INTERVAL, GETDATA_INTERVAL
from hoymilesapi import Hoymiles
from mqttapi import MqttApi
import threading, time, signal


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('HoymilesAdd-on')
logger.setLevel(logging.INFO)


def getEnv(env):
    ''' Get OS environment data'''
    ret = ""
    try:
        ret = os.environ[env]
    except:
        ret = ""
    return ret

def get_secrets():
    json_path = ""
    if os.path.isfile("./config.json"):
        json_path = "config.json"
    else:
        json_path = "/data/options.json"
    with open(json_path) as json_file:
        config = json.load(json_file)
        if 'options' in config.keys():
            config = config['options']
    if config['DEVELOPERS_MODE']:
        logger.setLevel(logging.DEBUG)
    return config


def json_remove_void(strJson):
    ''' remove linhas / elementos vazios de uma string Json '''
    strJson.replace("\n","")
    try:
        dados = json.loads(strJson)  # converte string para dict
    except Exception as e:
        if e.__class__.__name__ == 'JSONDecodeError':
            logger.warning ("erro json.load: " + strJson)
        else:
            logger.error("on_message")
    cp_dados = json.loads(strJson) # cria uma copia
    for k,v in dados.items():
        if len(v) == 0:
            cp_dados.pop(k)  # remove vazio
    return json.dumps(cp_dados) # converte dict para json


def monta_publica_topico(mqtt_h:MqttApi, component, sDict, varComuns):
    ''' monta e envia topico - sensores'''
    ret_rc = 0
    key_todos = sDict['todos']
    newDict = sDict.copy()
    newDict.pop('todos')
    for key,dic in newDict.items():
        # print(key,dic)
        if key[:1] != '#':
            varComuns['uniq_id']=varComuns['identifiers'] + "_" + key
            if not('val_tpl' in dic):
                dic['val_tpl'] = dic['name']
            dic['name'] = varComuns['uniq_id']
            dic['device_dict'] = device_dict
            dic['publish_time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            dic['expire_after'] = int(EXPIRE_TIME) # quando deve expirar
            dados = Template(json_hass[component]) # sensor
            dados = Template(dados.safe_substitute(dic))
            varComuns_template = Template( json.dumps(varComuns) )
            varComuns_template = varComuns_template.safe_substitute(varComuns) 
            dados = Template(dados.safe_substitute(json.loads( varComuns_template)) ) # faz ultimas substituições
            dados = dados.safe_substitute(key_todos) # remove os não substituidos.
            topico = MQTT_HASS + "/" + component + "/" + NODE_ID + "/" + varComuns['uniq_id'] + "/config"
            dados = json_remove_void(dados)
            (rc, mid) = mqtt_h.public(topico, dados)
            if rc == 0:
                topicoResumo = topico.replace(MQTT_HASS + "/" + component + "/" + NODE_ID, '...')
                topicoResumo = topicoResumo.replace("/config", '')
                logger.debug(topicoResumo)
                logger.debug(dados)
            else:
                logger.error("Erro monta_publica_topico")
                logger.error(topico)
            ret_rc = ret_rc + rc
    return rc


def send_hass(hoymiles_h: Hoymiles, mqtt_h: MqttApi):
    ''' Envia parametros para incluir device no hass.io '''
    sensor_dic={}
    # var comuns
    varComuns = {'sw_version': __version__,
                 'model': hoymiles_h.dtu,
                 'manufacturer': "asd",
                 'device_name': __app_name__,
                 'identifiers': SHORT_NAME + "_" + str(hoymiles_h.plant_id),
                 'via_device': hoymiles_h.dtu,
                 'sid': SID,
                 'plant_id': str(hoymiles_h.plant_id),
                 'uniq_id': mqtt_h.uuid } 
    
    logger.debug(f"Sensor_dic: {len(sensor_dic)}")

    if len(sensor_dic) == 0:
        for k in json_hass.items():
            json_file_path = k[0] + '.json'
            if not os.path.isfile(json_file_path):
                json_file_path = '/' + json_file_path  # to run on HASS.IO
            if not os.path.isfile(json_file_path):
                logger.error(json_file_path + " not found!")
            json_file = open(json_file_path)
            if not json_file.readable():
                logger.error("I can't read file")
            json_str = json_file.read()
            sensor_dic[k[0]] = json.loads(json_str)

    if len(sensor_dic) == 0:
        logger.error("Sensor_dic error")
    rc = 0
    for k in sensor_dic.items():
        # print('Componente:' + k[0])
        rc = monta_publica_topico(mqtt_h, k[0], sensor_dic[k[0]], varComuns)
        if not rc == 0:
            logger.error(f"Hass publish error: {rc}")

    if rc == 0:
        logger.debug('Hass Sended')


def publicaDadosWeb(hoymiles_h: Hoymiles, mqqt_t: MqttApi):
    # publica dados na web por meio do webserver via JSON
    jsonx = publicate_data(hoymiles_h, mqqt_t)
    # add new data
    json_load = json.loads(jsonx)
    json_load['last_time'] = hoymiles_h.data_dict['last_time']  
    json_load['load_cnt'] = hoymiles_h.data_dict['load_cnt']
    json_load['load_time'] = hoymiles_h.data_dict['load_time']
    json_x = json.dumps(json_load)
    return json_x


def publicate_data(hoymiles_h: Hoymiles, mqtt_h: MqttApi):
    # publica dados no MQTT  - MQTT_PUB/json
    hoymiles_h.get_solar_data()
    jsonUPS = json.dumps(hoymiles_h.solar_data)
    (rc, mid) = mqtt_h.public(MQTT_PUB + "/json" + '_' + str(hoymiles_h.plant_id), jsonUPS)
    mqtt_h.publicate_time = datetime.now()
    logger.info(f"Solar data publication...{datetime.now()}")
    # TODO: commented for tests
    mqtt_h.send_clients_status()
    return jsonUPS


class ProgramKilled(Exception):
    pass


def signal_handler(signum, frame):
    raise ProgramKilled


class Job(threading.Thread):
    def __init__(self, interval, execute, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs
        
    def stop(self):
                self.stopped.set()
                self.join()
    def run(self):
            while not self.stopped.wait(self.interval.total_seconds()):
                self.execute(*self.args, **self.kwargs)


def main() -> int:
    logger.info("********** " + __author__ + " " + __app_name__ + " v." + __version__)
    logger.info(f"Starting up... {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}")

    gEnvios = {'last_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            'load_cnt': 0,
            'load_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S')} 

    config = get_secrets()

    # v0.24.2 - by dms
    if (not config['External_MQTT_Server']):
        config['MQTT_Host'] = getEnv('MQTT_HOST_HA')
        config['MQTT_Pass'] = getEnv('MQTT_PASSWORD_HA')
        config['MQTT_User'] = getEnv('MQTT_USER_HA')
        logger.info(f"Using Internal MQTT Server: {str(config['MQTT_Host'])}")
        logger.info(f"Using Internal MQTT User: {str(config['MQTT_User'])}")
    else:
        logger.info(f"Using External MQTT Server: {str(config['External_MQTT_Server'])}")

    if int(config['HOYMILES_PLANT_ID']) < 100:
        logger.warning(f"Wrong plant ID {config['HOYMILES_PLANT_ID']}")

    hoymiles = Hoymiles(plant_id=int(config['HOYMILES_PLANT_ID']), config=config, gEnvios=gEnvios)

    if hoymiles.token != '':
        solar_data = hoymiles.get_solar_data()
    else:
        logger.error("I can't get access token")
        quit()

    mqtt = MqttApi(config)
    mqtt.start()
    while not mqtt.connected:
        time.sleep(1)  # wait for connection
        if not mqtt.client_status:
            time.sleep(240)

    send_hass(hoymiles, mqtt)

    publicate_data(hoymiles, mqtt)

    # TODO: commented for tests
    mqtt.send_clients_status()

    # if WEB_SERVER:  # se tiver webserver, inicia o web server
    #     iniciaWebServer()
    #     dl.writeJsonFile(FILE_COMM, jsonx)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    job_send_hass = Job(interval=timedelta(seconds=HASS_INTERVAL), execute=send_hass, hoymiles_h=hoymiles, mqtt_h=mqtt)
    job_send_hass.start()
    job_publicaDados = Job(interval=timedelta(seconds=GETDATA_INTERVAL), execute=publicate_data, hoymiles_h=hoymiles, mqtt_h=mqtt)
    job_publicaDados.start()

    logger.info("Main loop start!")
    while True:
        if not mqtt.connected:
            sys.exit()
        try:
            time.sleep(10)
        except ProgramKilled:
            logger.info("Program killed: running cleanup code")
            job_send_hass.stop()
            job_publicaDados.stop()
            break

    return 0


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit