"""
Main module of addon
"""
__author__ = 'dmslabs&Cosik'
__version__ = '0.24'
__app_name__ = 'Hoymiles Gateway'

import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timedelta
from string import Template

from const import (EXPIRE_TIME, GETDATA_INTERVAL, HASS_INTERVAL, MQTT_HASS,
                   MQTT_PUB, NODE_ID, SHORT_NAME, SID, DEVICE_DICT, json_hass)
from hoymilesapi import Hoymiles
from mqttapi import MqttApi

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('HoymilesAdd-on')
logger.setLevel(logging.INFO)


def get_secrets() -> dict:
    """Getting data from config json file

    Returns:
        dict: Config data in dict shape
    """
    json_path = ""
    if os.path.isfile("./config.json"):
        json_path = "config.json"
    else:
        json_path = "/data/options.json"
    with open(json_path, 'r', encoding="utf-8") as json_file:
        config = json.load(json_file)
        if 'options' in config.keys():
            config = config['options']
    if config['DEVELOPERS_MODE']:
        logger.setLevel(logging.DEBUG)
    return config


def json_remove_void(str_json):
    ''' remove linhas / elementos vazios de uma string Json '''
    str_json.replace("\n", "")
    try:
        dados = json.loads(str_json)  # converte string para dict
    except Exception as err:
        if err.__class__.__name__ == 'JSONDecodeError':
            logger.warning("erro json.load: %r", str_json)
        else:
            logger.error("on_message")
    cp_dados = json.loads(str_json)  # cria uma copia
    for key, value in dados.items():
        if len(value) == 0:
            cp_dados.pop(key)  # remove vazio
    return json.dumps(cp_dados)  # converte dict para json


def monta_publica_topico(mqtt_h: MqttApi, component, s_dict, var_comuns):
    ''' monta e envia topico - sensores'''
    ret_rc = 0
    key_todos = s_dict['todos']
    new_dict = s_dict.copy()
    new_dict.pop('todos')
    for key, dic in new_dict.items():
        # print(key,dic)
        if key[:1] != '#':
            var_comuns['uniq_id'] = var_comuns['identifiers'] + "_" + key
            if 'val_tpl' not in dic:
                dic['val_tpl'] = dic['name']
            dic['name'] = var_comuns['uniq_id']
            dic['device_dict'] = DEVICE_DICT
            dic['publish_time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            dic['expire_after'] = int(EXPIRE_TIME)  # quando deve expirar
            dados = Template(json_hass[component])  # sensor
            dados = Template(dados.safe_substitute(dic))
            var_comuns_template = Template(json.dumps(var_comuns))
            var_comuns_template = var_comuns_template.safe_substitute(var_comuns)
            # faz ultimas substituições
            dados = Template(dados.safe_substitute(
                json.loads(var_comuns_template)))
            # remove os não substituidos.
            dados = dados.safe_substitute(key_todos)
            topico = MQTT_HASS + "/" + component + "/" + \
                NODE_ID + "/" + var_comuns['uniq_id'] + "/config"
            dados = json_remove_void(dados)
            ret_code = mqtt_h.public(topico, dados)
            if ret_code == 0:
                topico_resumo = topico.replace(
                    MQTT_HASS + "/" + component + "/" + NODE_ID, '...')
                topico_resumo = topico_resumo.replace("/config", '')
                logger.debug(topico_resumo)
                logger.debug(dados)
            else:
                logger.error("Erro monta_publica_topico")
                logger.error(topico)
            ret_rc = ret_rc + ret_code
    return ret_code


def send_hass(hoymiles_h: Hoymiles, mqtt_h: MqttApi):
    ''' Envia parametros para incluir device no hass.io '''

    var_comuns = {}
    var_comuns = {'dtu': {'sw_version': hoymiles_h.dtu.soft_ver,
                         'model': hoymiles_h.dtu.model_no,
                         'manufacturer': "asd",
                         'device_name': __app_name__,
                         'identifiers': SHORT_NAME + "_" + str(hoymiles_h.plant_id),
                         'via_device': hoymiles_h.dtu.id,
                         'sid': SID,
                         'plant_id': str(hoymiles_h.plant_id),
                         'uniq_id': hoymiles_h.dtu.uuid}}
    for micro in hoymiles_h.device_list:
        var_comuns.update({f"micro_{micro.id}": {'sw_version': micro.soft_ver,
                                                'model': micro.init_hard_no,
                                                'manufacturer': "asd",
                                                'device_name': __app_name__,
                                                'identifiers': SHORT_NAME + "_" + str(micro.id),
                                                'via_device': micro.id,
                                                'sid': SID,
                                                'plant_id': str(hoymiles_h.plant_id),
                                                'uniq_id': micro.uuid}})

    for device in var_comuns:
        sensor_dic = {}
        if '_' in device:
            json_file_path = device.split('_')[0] + '.json'
        else:
            json_file_path = device + '.json'
        if not os.path.isfile(json_file_path):
            json_file_path = '/' + json_file_path  # to run on HASS.IO
        if not os.path.isfile(json_file_path):
            logger.error("%r not found!", json_file_path)
        with open(json_file_path, 'r', encoding="utf-8") as json_file:
            if not json_file.readable():
                logger.error("I can't read file")

            # json_str = json_file.read()
            data = json.load(json_file)
            for k in json_hass.items():
                try:
                    sensor_dic[k[0]] = data[k[0]]
                except Exception as err:
                    logger.debug(f"{err}")

        if len(sensor_dic) == 0:
            logger.error("Sensor_dic error")
        ret_code = 0
        for k in sensor_dic.items():
            # print('Componente:' + k[0])
            ret_code = monta_publica_topico(
                mqtt_h, k[0], sensor_dic[k[0]], var_comuns[device])
            if not ret_code == 0:
                logger.error(f"Hass publish error: {ret_code}")

        if ret_code == 0:
            logger.debug(f'Hass Sended for {device}')


def publicate_data(hoymiles_h: Hoymiles, mqtt_h: MqttApi):
    """Publicate date over mqqt from passed farm

    Args:
        hoymiles_h (Hoymiles): Passed farm from which data will be sedn
        mqtt_h (MqttApi): Handler to mqtt server connection
    """
    # publica dados no MQTT  - MQTT_PUB/json
    hoymiles_h.update_devices_status()
    hoymiles_h.get_solar_data()
    json_ups = json.dumps(hoymiles_h.solar_data)
    mqtt_h.public(MQTT_PUB + "/json" +
                  '_' + str(hoymiles_h.dtu.id), json_ups)
    mqtt_h.publicate_time = datetime.now()
    logger.info(f"Solar data publication...{datetime.now()}")
    mqtt_h.send_clients_status()
    for device in hoymiles_h.device_list:
        data = {'connect': device.connect}
        json_ups = json.dumps(data)
        mqtt_h.public(MQTT_PUB +
                                  "/json" + '_' + str(device.id), json_ups)
        mqtt_h.publicate_time = datetime.now()
        logger.info(
            f"{device.init_hard_no}_{device.id} data publication...{datetime.now()}")
        mqtt_h.send_clients_status()
    return


class ProgramKilled(Exception):
    """Programm killer
    """
    empty = None


def signal_handler(signum, frame):
    """Signal handler

    Args:
        signum (_type_): _description_
        frame (_type_): _description_

    Raises:
        ProgramKilled: _description_
    """
    raise ProgramKilled


class Job(threading.Thread):
    """Custom class to handle running mathods and save resources
    """
    def __init__(self, interval, execute, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs

    def stop(self):
        """Stop job
        """
        self.stopped.set()
        self.join()

    def run(self):
        """Run job
        """
        while not self.stopped.wait(self.interval.total_seconds()):
            self.execute(*self.args, **self.kwargs)


def main() -> int:
    """Main function of script

    """
    logger.info(f"********** {__author__} {__app_name__}  v.{__version__}")
    logger.info(
        f"Starting up... {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}")

    g_envios = {'last_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
               'load_cnt': 0,
               'load_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S')}

    config = get_secrets()

    if int(config['HOYMILES_PLANT_ID']) < 100:
        logger.warning(f"Wrong plant ID {config['HOYMILES_PLANT_ID']}")

    hoymiles = Hoymiles(plant_id=int(
        config['HOYMILES_PLANT_ID']), config=config, g_envios=g_envios)

    if hoymiles.token == '':
        logger.error("I can't get access token")
        quit()

    if not hoymiles.verify_plant():
        logger.error("User has no access to plant")
        quit()

    hoymiles.get_plant_hw()
    while not hoymiles.dtu.connect:
        time.sleep(600)
        hoymiles.get_plant_hw()

    mqtt = MqttApi(config, hoymiles)
    mqtt.start()
    while not mqtt.connected:
        time.sleep(1)  # wait for connection
        if not mqtt.client_status:
            time.sleep(240)

    send_hass(hoymiles, mqtt)

    publicate_data(hoymiles, mqtt)

    mqtt.send_clients_status()

    # if WEB_SERVER:  # se tiver webserver, inicia o web server
    #     iniciaWebServer()
    #     dl.writeJsonFile(FILE_COMM, jsonx)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    job_send_hass = Job(interval=timedelta(seconds=HASS_INTERVAL),
                        execute=send_hass, hoymiles_h=hoymiles, mqtt_h=mqtt)
    job_send_hass.start()
    job_publica_dados = Job(interval=timedelta(
        seconds=GETDATA_INTERVAL), execute=publicate_data, hoymiles_h=hoymiles, mqtt_h=mqtt)
    job_publica_dados.start()

    logger.info("Main loop start!")
    while True:
        if not mqtt.connected:
            sys.exit()
        try:
            time.sleep(10)
        except ProgramKilled:
            logger.info("Program killed: running cleanup code")
            job_send_hass.stop()
            job_publica_dados.stop()
            break

    return 0


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit
