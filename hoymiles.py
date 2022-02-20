__author__ = 'dmslabs'
__version__ = '0.23'
__app_name__ = 'Hoymiles Gateway'

import logging
import os
import sys
from datetime import datetime
from configparser import ConfigParser
import time
import json
from string import Template


from const import SECRETS, SHORT_NAME, SID, json_hass, MQTT_HASS, device_dict, EXPIRE_TIME, NODE_ID, MQTT_PUB
from hoymilesapi import Hoymiles
from mqttapi import MqttApi


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('HoymilesAdd-on')
logger.setLevel(logging.INFO)


def getConfigParser(secrets_file):
    logger.info("Getting Config Parser.")
    asdasd = os.path.isfile(secrets_file)
    # if asdasd:
    #     logger.debug(f"exist {secrets_file}")

    # else:
    #     logger.warning(f"Not existing {secrets_file}")

    config = ConfigParser()

    try:
        config.read(secrets_file)
    except Exception as e:
        logger.warning("Can't load config. Using default config.")
    return config


def get_secrets():
    config = getConfigParser(SECRETS)

    logger.info("Reading secrets.ini")

    if config.getboolean('developers', 'DEVELOPERS_MODE'):
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
            #dados = Template(dados.safe_substitute(varComuns)) # faz ultimas substituições
            dados = Template(dados.safe_substitute(json.loads( varComuns_template)) ) # faz ultimas substituições
            dados = dados.safe_substitute(key_todos) # remove os não substituidos.
            topico = MQTT_HASS + "/" + component + "/" + NODE_ID + "/" + varComuns['uniq_id'] + "/config"
            # print(topico)
            # print(dados)
            dados = json_remove_void(dados)
            (rc, mid) = mqtt_h.public(topico, dados)
            if rc == 0:
                # if DEVELOPERS_MODE:
                topicoResumo = topico.replace(MQTT_HASS + "/" + component + "/" + NODE_ID, '...')
                topicoResumo = topicoResumo.replace("/config", '')
                logger.debug(topicoResumo)
                logger.debug(dados)
            else:
                # deu erro na publicação
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
                 'last_reset_topic': 'home/$sid/json_$plant_id',
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
        # gDevices_enviados['b'] = True
        # gDevices_enviados['t'] = datetime.now()
        logger.debug('Hass Sended')



def publicaDadosWeb(hoymiles_h: Hoymiles, mqqt_t: MqttApi):
    # publica dados na web por meio do webserver via JSON
    jsonx = publicaDados(hoymiles_h, mqqt_t)
    # add new data
    json_load = json.loads(jsonx)
    json_load['last_time'] = hoymiles_h.data_dict['last_time']  
    json_load['load_cnt'] = hoymiles_h.data_dict['load_cnt']
    json_load['load_time'] = hoymiles_h.data_dict['load_time']
    json_x = json.dumps(json_load)
    return json_x


def publicaDados(hoymiles_h: Hoymiles, mqqt_h: MqttApi):
    # publica dados no MQTT  - MQTT_PUB/json
    jsonUPS = json.dumps(hoymiles_h.solar_data)
    (rc, mid) = mqqt_h.public(MQTT_PUB + "/json" + '_' + str(hoymiles_h.plant_id), jsonUPS)
    mqqt_h.publicate_time = datetime.now()
    logger.info(f"Dados Solares Publicados...{datetime.now()}")
    mqqt_h.send_clients_status()
    return jsonUPS


def main() -> int:
    # INICIO, START

    logger.info("********** " + __author__ + " " + __app_name__ + " v." + __version__)
    logger.info(f"Starting up... {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}")

    gEnvios = {'last_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            'load_cnt': 0,
            'load_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S')} 

    config = get_secrets()

    if int(config.get('secrets','HOYMILES_PLANT_ID')) < 100:
        logger.warning(f"Wrong plant ID {config.get('secrets','HOYMILES_PLANT_ID')}")

    hoymiles = Hoymiles(plant_id=int(config.get('secrets','HOYMILES_PLANT_ID')), config=config, gEnvios=gEnvios)

    if hoymiles.token != '':
        solar_data = hoymiles.get_solar_data()
    else:
        logger.error("I can't get access token")
        quit()


            # # força a conexão
    mqtt = MqttApi(config, gEnvios=gEnvios)
    mqtt.start()
    while not mqtt.connected:
        time.sleep(1)  # wait for connection
        if not mqtt.client_status:
            time.sleep(240)


    send_hass(hoymiles, mqtt)


    jsonx = publicaDadosWeb(hoymiles, mqtt)

    mqtt.send_clients_status()


    # if WEB_SERVER:  # se tiver webserver, inicia o web server
    #     iniciaWebServer()
    #     dl.writeJsonFile(FILE_COMM, jsonx)

    logger.info("Main loop start!")
    while True:
        if gConnected:
            time_dif = dl.date_diff_in_Seconds(datetime.now(), \
                gDevices_enviados['t'])
            if time_dif > INTERVALO_HASS:
                gDevices_enviados['b'] = False
                send_hass()
            time_dif = dl.date_diff_in_Seconds(datetime.now(), \
                gMqttEnviado['t'])
            if time_dif > INTERVALO_GETDATA:
                pegaDadosSolar()
                jsonx = publicaDadosWeb(gDadosSolar, HOYMILES_PLANT_ID)
                if WEB_SERVER:
                    dl.writeJsonFile(FILE_COMM, jsonx)
            if not clientOk: mqttStart()  # tenta client mqqt novamente.
        time.sleep(10) # dá um tempo de 10s



    # TODO: is it need?
    # version check
    # if int(dl.version()) < int(version_expected['dmslibs']):
    #     printC (Color.B_Red, "Wrong dmslibs version! ")
    #     printC (Color.F_Blue, "Current: " + dl.version() )
    #     printC (Color.F_Blue, "Expected: " + version_expected['dmslibs'] )



    # # info
    # dl.dadosOS()
    # status['ip'] = dl.get_ip()
    # print (Color.B_Cyan + "IP: " + Color.B_Default + Color.F_Magenta + status['ip'] + Color.F_Default)
    # if DEVELOPERS_MODE:
    #     print (Color.B_Red, "DEVELOPERS_MODE", Color.B_Default)

    # get_secrets()

    # if dl.IN_HASSIO():
    #     print (Color.B_Blue, "IN HASS.IO", Color.B_Default)
    #     if not DEVELOPERS_MODE or 1==1:  # teste
    #         substitui_secrets()
    #         if DEVELOPERS_MODE:
    #             print (Color.B_Red, "DEVELOPERS_MODE", Color.B_Default)
    #     if DEFAULT_MQTT_PASS == MQTT_PASSWORD:
    #         log().warning ("YOU SHOUD CHANGE DE DEFAULT MQTT PASSWORD!")
    #         print (Color.F_Red + "YOU SHOUD CHANGE DE DEFAULT MQTT PASSWORD!" + Color.F_Default)


    # if DEVELOPERS_MODE or MQTT_HOST == '192.168.50.20':
    #     print (Color.F_Green + "HOYMILES_USER: " + Color.F_Default + str(HOYMILES_USER))
    #     print (Color.F_Green + "HOYMILES_PASSWORD: " + Color.F_Default + str(HOYMILES_PASSWORD))
    #     print (Color.F_Green + "HOYMILES_PLANT_ID: " + Color.F_Default + str(HOYMILES_PLANT_ID))
    #     print (Color.F_Green + "MQTT_HOST: " + Color.F_Default + str(MQTT_HOST))
    #     print (Color.F_Green + "MQTT_PASSWORD: " + Color.F_Default + str(MQTT_PASSWORD))
    #     print (Color.F_Green + "MQTT_USERNAME: " + Color.F_Default + str(MQTT_USERNAME))
    #     print (Color.F_Blue + "INTERVALO_MQTT: " + Color.F_Default + str(INTERVALO_MQTT))
    #     print (Color.F_Blue + "INTERVALO_HASS: " + Color.F_Default + str(INTERVALO_HASS))
    #     print (Color.F_Blue + "INTERVALO_GETDATA: " + Color.F_Default + str(INTERVALO_GETDATA))
    #     print (Color.F_Blue + "WEB_SERVER: " + Color.F_Default + str(WEB_SERVER))

    # if dl.float2number(HOYMILES_PLANT_ID) < 100:        
    #     print (Color.F_Green + "HOYMILES_PLANT_ID: " + Color.F_Default + str(HOYMILES_PLANT_ID))
    #     print (Color.B_Magenta + "Wrong plant ID" + Color.B_Default )

    # cnt = 0
    # hoymiles = HoymilesAPI(plant_id=int(HOYMILES_PLANT_ID))


    # if hoymiles.token != '':
    #     # pega dados solar
    #     #dados_solar = pega_solar(HOYMILES_PLANT_ID)
    #     #print (str(dados_solar))
    #     #gDadosSolar = dados_solar['data']
    #     solar_data = hoymiles.get_solar_data()
    # else:
    #     log().error("I can't get access token")
    #     print (Color.B_Red + "I can't get access token" + Color.B_Default)
    #     quit()

    # # força a conexão
    # while not gConnected:
    #     mqttStart()
    #     time.sleep(1)  # wait for connection
    #     if not clientOk:
    #         time.sleep(240)

    # send_hass()

    # # primeira publicação
    # jsonx = publicaDadosWeb(solar_data, HOYMILES_PLANT_ID)

    # if dl.float2number(solar_data['total_eq'], 0) == 0:
    #     log().warning('All data is 0. Maybe your Plant_ID is wrong.')
    #     status['response'] = "Plant_ID could be wrong!"

    # send_clients_status()


    # if WEB_SERVER:  # se tiver webserver, inicia o web server
    #     iniciaWebServer()
    #     dl.writeJsonFile(FILE_COMM, jsonx)


    # printC(Color.B_LightCyan, 'Loop start!')
    # # loop start
    # while True:
    #     if gConnected:
    #         time_dif = dl.date_diff_in_Seconds(datetime.now(), \
    #             gDevices_enviados['t'])
    #         if time_dif > INTERVALO_HASS:
    #             gDevices_enviados['b'] = False
    #             send_hass()
    #         time_dif = dl.date_diff_in_Seconds(datetime.now(), \
    #             gMqttEnviado['t'])
    #         if time_dif > INTERVALO_GETDATA:
    #             solar_data = hoymiles.get_solar_data()
    #             jsonx = publicaDadosWeb(gDadosSolar, HOYMILES_PLANT_ID)
    #             if WEB_SERVER:
    #                 dl.writeJsonFile(FILE_COMM, jsonx)
    #         if not clientOk: mqttStart()  # tenta client mqqt novamente.
    #     time.sleep(10) # dá um tempo de 10s



    return 0




if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit