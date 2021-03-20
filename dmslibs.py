__author__ = 'dmslabs'

# Commum methods and functions

import logging
import os
import sys
import pathlib

# CONSTANTS
# ARRUMAR aqui para não ficar na lib


# VARS GLOBAIS
log = ''

def getConfigParser(secrets_file):
    ''' Pega o Config Parcer '''
    print ("Getting Config Parser.")
    bl_existe_secrets = os.path.isfile(secrets_file)
    if bl_existe_secrets:
        log.debug("Existe " + secrets_file)
        print ("Existe " +  secrets_file)
    else:
        log.warning("Não existe " + secrets_file)
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
        log.warning("Can't load config. Using default config.")
        print ("Can't load config. Using default config.")
        mostraErro(e,20, "get_secrets")
        # ver - INFO get_secrets / Error! Code: DuplicateOptionError, Message,
        #  While reading from 'secrets.ini' [line 22]: option 'log_file' in section 'config' 
        # already exists
    return config


def inicia_log(logFile, logName = "dmsLibs", stdOut = True, logLevel = logging.DEBUG):
    ''' inicia o log do sistema '''
    global log
    if stdOut:
        log = iniciaLoggerStdout()
    else:
        log = iniciaLogger(logFile, logLevel, logName)


def iniciaLoggerStdout():
    ''' inicia loggger no StdOut '''
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log

def iniciaLogger(logFile, logLevel, logName):
    ''' inicia loggger no LOG_FILE '''
    log = logging.getLogger(logName) # 'smsUPS'
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
        log.addHandler(hdlr) 
        log.setLevel(logLevel)
    if erroDif != False:
        # different error
        mostraErro(e, 20, 'Open LOG_FILE')
    if hdlr.baseFilename != logFile:
        print ('LOG file: ', hdlr.baseFilename)
        log.debug ('LOG file: ' + hdlr.baseFilename)
    return log



def get_config (config, topic, key, default, getBool = False, getInt = False, split = False):
    ''' Read config data '''
    ret = default
    try:
        ret = config.get(topic, key)
        if getBool or type(default) is bool: ret = config.getboolean(topic, key)
        if getInt or type(default) is int: ret = config.getint(topic, key)
    except:
        ret = default
        log.debug('Config: ' + key + " use default: " + str(default))
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
    if nivel == logging.DEBUG: log.debug(err_msg)      # 10
    if nivel == logging.INFO: log.info(err_msg)       # 20
    if nivel == logging.WARNING: log.warning(err_msg)    # 30
    if nivel == logging.ERROR: log.error(err_msg)      # 40
    if nivel == logging.CRITICAL: log.critical(err_msg)   # 50

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

def pegaEnv(env):
    ''' PEGA dados do ENV do SO '''
    ret = ""
    try:
        ret = os.environ[env]
    except:
        ret = ""
    return ret

# HASS.IO Functions

def IN_HASSIO():
    ''' retorna true se estiver dentro do HASS.IO '''
    PATH_ROOT = pathlib.Path().absolute()
    PATH_ROOT = str(PATH_ROOT.resolve())
    inHass = ( pegaEnv('HASSIO_TOKEN') != "" and PATH_ROOT == "/data")
    return inHass
