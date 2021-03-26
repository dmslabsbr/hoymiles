__author__ = 'dmslabs'

# Commum methods and functions

import logging
import os
import sys
import pathlib
import socket
import requests
import json

# CONSTANTS
# ARRUMAR aqui para não ficar na lib

# Constants que podem ficar na lib

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
    403: "Forbidden",  
    403: "Forbidden",  
    504: "Gateway Timeout",
    1000: "Message not set."
    }

MQTT_STATUS_CODE = {
    0: "Connection successful",
    1: "Connection refused – incorrect protocol version",
    2: "Connection refused – invalid client identifier",
    3: "Connection refused – server unavailable",
    4: "Connection refused – bad username or password",
    5: "Connection refused – not authorised",
    100: "Connection refused - other things"
    }

# VARS GLOBAIS
_log = ''

def log():
    return _log 

def getConfigParser(secrets_file):
    ''' Pega o Config Parcer '''
    print ("Getting Config Parser.")
    bl_existe_secrets = os.path.isfile(secrets_file)
    if bl_existe_secrets:
        _log.debug("Existe " + secrets_file)
        print ("Existe " +  secrets_file)
    else:
        _log.warning("Não existe " + secrets_file)
        print (Color.F_Magenta, "Não existe " +  secrets_file, Color.F_Default)
        # SECRETS = "/" + SECRETS # tenta arrumar para o HASS.IO
        # O ideal é o SECRETS ficar no data, para não perder a cada iniciada.

    try:
        from configparser import ConfigParser
        config = ConfigParser()
    except ImportError:
        from configparser import ConfigParser  # ver. < 3.0   // era ConfigParser UPPER C e P
    try:
        config.read(secrets_file)
    except Exception as e:
        _log.warning("Can't load config. Using default config.")
        print ("Can't load config. Using default config.")
        mostraErro(e,20, "get_secrets")
        # ver - INFO get_secrets / Error! Code: DuplicateOptionError, Message,
        #  While reading from 'secrets.ini' [line 22]: option 'log_file' in section 'config' 
        # already exists
    return config


def inicia_log(logFile, logName = "dmsLibs", stdOut = True, logLevel = logging.DEBUG):
    ''' inicia o log do sistema '''
    global _log
    if stdOut:
        _log = iniciaLoggerStdout()
    else:
        _log = iniciaLogger(logFile, logLevel, logName)


def iniciaLoggerStdout():
    ''' inicia loggger no StdOut '''
    _log = logging.getLogger()
    _log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    _log.addHandler(handler)
    return _log

def iniciaLogger(logFile, logLevel, logName):
    ''' inicia loggger no LOG_FILE '''
    _log = logging.getLogger(logName) # 'smsUPS'
    erroDif = False
    try:
        hdlr = logging.FileHandler(logFile)
    except PermissionError:  # caso não consiga abrir
        hdlr = logging.FileHandler('./' + logName + '.log')
    except Exception as e:
        erroDif = e
    finally:
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        _log.addHandler(hdlr) 
        _log.setLevel(logLevel)
    if erroDif != False:
        # different error
        mostraErro(e, 20, 'Open LOG_FILE')
    if hdlr.baseFilename != logFile:
        print ('LOG file: ', hdlr.baseFilename)
        _log.debug ('LOG file: ' + hdlr.baseFilename)
    return _log



def get_config (config, topic, key, default, getBool = False, getInt = False, split = False):
    ''' Read config data '''
    ret = default
    try:
        ret = config.get(topic, key)
        if getBool or type(default) is bool: ret = config.getboolean(topic, key)
        if getInt or type(default) is int: ret = config.getint(topic, key)
    except:
        ret = default
        _log.debug('Config: ' + key + " use default: " + str(default))
    if split:
        ret = ret.split(',')
        for i in range(len(ret)):
            ret[i] = ret[i].replace('"','').replace("'", '')
            ret[i] = ret[i].strip()
    return ret


def mostraErro(e, nivel=10, msg_add=""):
    ''' mostra erros '''
    err_msg = msg_add + ' / Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e))
    print(Color.F_Red + err_msg + Color.F_Default)
    if nivel == logging.DEBUG: _log.debug(err_msg)      # 10
    if nivel == logging.INFO: _log.info(err_msg)       # 20
    if nivel == logging.WARNING: _log.warning(err_msg)    # 30
    if nivel == logging.ERROR: _log.error(err_msg)      # 40
    if nivel == logging.CRITICAL: _log.critical(err_msg)   # 50

class Color:
    # Foreground
    F_Default = "\x1b[39m"
    F_Black = "\x1b[30m"
    F_Red = "\x1b[31m"
    F_Green = "\x1b[32m"
    F_Yellow = "\x1b[33m"
    F_Blue = "\x1b[34m"
    F_Magenta = "\x1b[35m"
    F_Cyan = "\x1b[36m"
    F_LightGray = "\x1b[37m"
    F_DarkGray = "\x1b[90m"
    F_LightRed = "\x1b[91m"
    F_LightGreen = "\x1b[92m"
    F_LightYellow = "\x1b[93m"
    F_LightBlue = "\x1b[94m"
    F_LightMagenta = "\x1b[95m"
    F_LightCyan = "\x1b[96m"
    F_White = "\x1b[97m"
    # Background
    B_Default = "\x1b[49m"
    B_Black = "\x1b[40m"
    B_Red = "\x1b[41m"
    B_Green = "\x1b[42m"
    B_Yellow = "\x1b[43m"
    B_Blue = "\x1b[44m"
    B_Magenta = "\x1b[45m"
    B_Cyan = "\x1b[46m"
    B_LightGray = "\x1b[47m"
    B_DarkGray = "\x1b[100m"
    B_LightRed = "\x1b[101m"
    B_LightGreen = "\x1b[102m"
    B_LightYellow = "\x1b[103m"
    B_LightBlue = "\x1b[104m"
    B_LightMagenta = "\x1b[105m"
    B_LightCyan = "\x1b[106m"
    B_White = "\x1b[107m"

def printC(cor, texto):
    ''' Imprime de uma cor '''
    corDict = Color.__dict__
    color = ''
    codProc = '\x1b'
    cor_default = ''
    # precisa dividir
    #if cor.count('[') == 1:
    #    color = list(corDict.keys())[list(corDict.values()).index(cor)]
    #else: 
    corDividida = cor.split(codProc)
    corDividida.pop(0)
    #corDividida[0] = codProc + corDividida[0]
    #corDividida[1] = codProc + corDividida[1]
    for i in range(len(corDividida)):
        corDividida[i] = codProc + corDividida[i]
        color = list(corDict.keys())[list(corDict.values()).index(corDividida[i])]
        if color[0] == "F":
            cor_default = cor_default + Color.F_Default
        else:
            cor_default = cor_default + Color.B_Default

    print (cor + texto + cor_default)

def pegaEnv(env):
    ''' PEGA dados do ENV do SO '''
    ret = ""
    try:
        ret = os.environ[env]
    except:
        ret = ""
    return ret

def get_ip(change_dot = False, testIP = '192.168.1.1'):
    ''' pega o IP do device '''
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


def dadosOS():
    ''' tenta pegar dados do SO '''
    ret = dict()
    try:
        osEnv = os.environ
        ret['os.name'] = str(os.name)
        ret['os.getlogin'] = str(os.getlogin())
        ret['os.uname'] = str(os.uname())
        ret['whoami'] = str(os.popen('whoami').read())
        _log.info("os.name: " + str(os.name))
        _log.info("os.getlogin: " + str(os.getlogin()))
        _log.info("os.uname: " + str(os.uname()))
        _log.info("whoami: " + str(os.popen('whoami').read()))
    except Exception as e:
        mostraErro(e, 10, 'info')
    return ret


def httpStatusCode(stCode):
    ''' retorna texto do status code '''
    ret = ''
    stCode = int(stCode)
    if stCode in HTTP_STATUS_CODE.keys():
        ret = HTTP_STATUS_CODE[stCode]
    else:
        ret = HTTP_STATUS_CODE[1000]
    return ret

def mqttStatusCode(stCode):
    ''' retorna texto do status code '''
    ret = ''
    stCode = int(stCode)
    if stCode in MQTT_STATUS_CODE.keys():
        ret = MQTT_STATUS_CODE[stCode]
    else:
        ret = MQTT_STATUS_CODE[100]
    return ret


def date_diff_in_Seconds(dt2, dt1):
    # Get time diference in seconds
    # not tested for many days.
  timedelta = dt2 - dt1
  return timedelta.days * 24 * 3600 + timedelta.seconds

def pega_url(url, payload, headers, debug_mode = False):
    print(Color.B_Green + "Loading: " + Color.B_Default + url)
    response = requests.request("POST", url, headers=headers, data = payload)
    ret = ""
    if response.status_code != 200:
        print (Color.F_Red + "Erro ao acessar: " + Color.F_Default + url)
        print(Color.F_Red + "status_code: " + Color.F_Default + str(response.status_code) + " " + httpStatusCode(response.status_code))
    else:
        ret = response.content
        if debug_mode:
            print("content: " + str(response.content))
    return ret, response.status_code

def pega_url2(url, payload, headers, debug_mode = False):
    print(Color.B_Green + "Loading: " + Color.B_Default + url)
    s = requests.Session()
    req = requests.Request('POST', url, data = payload.replace('\n',""), headers=headers)
    prepped = req.prepare()
    if debug_mode:
        print (prepped.headers)
    #response = requests.request("POST", url, headers=headers, data = payload)
    response = s.send(prepped)
    ret = ""
    if response.status_code != 200:
        print (Color.F_Red + "Erro ao acessar: " + Color.F_Default + url)
        print(Color.F_Red + "status_code: " + Color.F_Default + str(response.status_code) + " " + httpStatusCode(response.status_code))
    else:
        ret = response.content
        if debug_mode:
            print("content: " + str(response.content))
    return ret, response.status_code


def json_remove_vazio(strJson):
    ''' remove linhas / elementos vazios de uma string Json '''
    strJson.replace("\n","")
    try:
        dados = json.loads(strJson)  # converte string para dict
    except Exception as e:
        if e.__class__.__name__ == 'JSONDecodeError':
            log.warning ("erro json.load: " + strJson)
        else:
            mostraErro(e, 40, "on_message")
    cp_dados = json.loads(strJson) # cria uma copia
    for k,v in dados.items():
        if len(v) == 0:
            cp_dados.pop(k)  # remove vazio
    return json.dumps(cp_dados) # converte dict para json


def float2number(numero, arredonda = False):
    ''' Converte um número ou string '533.12341' para número normal '''
    fl = float(numero)
    ret = fl
    if arredonda != False:
        ret = round(fl,arredonda)
    return ret


def onOff(value, ON = "on", OFF = "off"):
    ''' return a string on / off '''
    v = str(value).upper().replace('-','')
    ret = OFF
    if v == '1': ret = ON
    if v == 'TRUE': ret = ON
    if v == 'ON': ret = ON
    return ret

# HASS.IO Functions

def IN_HASSIO():
    ''' retorna true se estiver dentro do HASS.IO '''
    PATH_ROOT = pathlib.Path().absolute()
    PATH_ROOT = str(PATH_ROOT.resolve())
    inHass = ( pegaEnv('HASSIO_TOKEN') != "" and PATH_ROOT == "/data")
    return inHass

