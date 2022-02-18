__author__ = 'dmslabs'
__version__ = '0.23'
__app_name__ = 'Hoymiles Gateway'

import logging
import os
import sys
from datetime import datetime, timezone
from configparser import ConfigParser


from const import SECRETS
from hoymilesapi import Hoymiles


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('HoymilesAdd-on')
logger.setLevel(logging.INFO)


logger.info("Getting Config Parser.")


def getConfigParser(secrets_file):
    ''' Pega o Config Parcer '''
    logger.info("Getting Config Parser.")
    if os.path.isfile(secrets_file):
        logger.debug(f"exist {secrets_file}")
    else:
        logger.warning(f"Not existing {secrets_file}")

    
    config = ConfigParser()

    try:
        config.read(secrets_file)
    except Exception as e:
        logger.warning("Can't load config. Using default config.")
    return config


def get_config (config, topic, key, default, getBool = False, getInt = False, split = False):
    ''' Read config data '''
    ret = default
    try:
        ret = config.get(topic, key)
        if getBool or type(default) is bool: ret = config.getboolean(topic, key)
        if getInt or type(default) is int: ret = config.getint(topic, key)
    except:
        ret = default
        logger.debug(f"Config: {key} use default: {default}")
    if split:
        ret = ret.split(',')
        for i in range(len(ret)):
            ret[i] = ret[i].replace('"','').replace("'", '')
            ret[i] = ret[i].strip()
    return ret

def get_secrets():
    config = getConfigParser(SECRETS)

    logger.info("Reading secrets.ini")

    if bool(config.get('developers', 'DEVELOPERS_MODE')) == True:
        logger.setLevel(logging.DEBUG)

    return config

    # le os dados
    HOYMILES_USER  = get_config(config, 'secrets', 'HOYMILES_USER', HOYMILES_USER)
    HOYMILES_PASSWORD = get_config(config, 'secrets', 'HOYMILES_PASSWORD', HOYMILES_PASSWORD)
    HOYMILES_PLANT_ID = get_config(config, 'secrets','HOYMILES_PLANT_ID', HOYMILES_PLANT_ID, getInt=True)
    MQTT_PASSWORD = get_config(config, 'secrets', 'MQTT_PASS', MQTT_PASSWORD)
    MQTT_USERNAME  = get_config(config, 'secrets', 'MQTT_USER', MQTT_USERNAME)
    MQTT_HOST = get_config(config, 'secrets', 'MQTT_HOST', MQTT_HOST)
    dev_mode = get_config(config, 'developers', 'DEVELOPERS_MODE', "")
    if bool(config.get(config, 'developers')) == True:
        logger.setLevel(logging.DEBUG)
    else:
        DEVELOPERS_MODE = False
    WEB_SERVER = get_config(config, 'secrets', 'WEB_SERVER', WEB_SERVER)
    # external server
    External_MQTT_Server = get_config(config, 'external', 'External_MQTT_Server', External_MQTT_Server, getBool=True)
    if (External_MQTT_Server):
        External_MQTT_Host = get_config(config, 'external', 'External_MQTT_Host', External_MQTT_Host)
        External_MQTT_User = get_config(config, 'external', 'External_MQTT_User', External_MQTT_User)
        External_MQTT_Pass = get_config(config, 'external', 'External_MQTT_Pass', External_MQTT_Pass)
        External_MQTT_TLS = get_config(config, 'external', 'External_MQTT_TLS', External_MQTT_TLS, getBool=True)
        External_MQTT_TLS_PORT = get_config(config, 'external', 'External_MQTT_TLS_PORT', External_MQTT_TLS_PORT, getInt=True)
    if (External_MQTT_Server):
        MQTT_HOST = External_MQTT_Host
        MQTT_PASSWORD = External_MQTT_Pass
        MQTT_USERNAME = External_MQTT_User
        logger.info(f"Using External MQTT Server: {MQTT_HOST}")
        if (External_MQTT_TLS):
            MQTT_PORT = External_MQTT_TLS_PORT
            logger.info(f"Using External MQTT TLS PORT: {MQTT_PORT}")
    else:
        External_MQTT_TLS = False

    return config



def main() -> int:
    # INICIO, START

    logger.info("********** " + __author__ + " " + __app_name__ + " v." + __version__)
    logger.info(f"Starting up... {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}")

    config = get_secrets()

    if int(config.get('secrets','HOYMILES_PLANT_ID')) < 100:
        logger.warning(f"Wrong plant ID {config.get('secrets','HOYMILES_PLANT_ID')}")

    hoymiles = Hoymiles(plant_id=int(config.get('secrets','HOYMILES_PLANT_ID')), config=config)

    if hoymiles.token != '':
        solar_data = hoymiles.get_solar_data()
    else:
        logger.error("I can't get access token")
        quit()

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