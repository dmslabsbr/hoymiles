# CHANGELOG

## 1.4

- In the Edge release, we’ve upgraded the minimal image base to Python 3.10-alpine3.18.
- Additionally, we’ve addressed an issue related to internet failures when sending payloads.

## 1.3

- Support bms/batteries

## 1.2

- Support for multiple installations
- Support HM meter reading
- Reduce time of sending mqtt msg
- Fixed the problem that caused LOG level parameters not to be loaded.
- Fixed the issue that does not allow the connection status to be updated.

## 1.1

- Release edge

## 1.00

- Added support for reading all devices
- Each device is separate MQTT decvice.
- Bump image to alpine3.13.
- Added sending alarms form inverters.
- Added year production read.
- Added real power in kW.
- Removed duplicated commands during build docker image.
- Added logging to file.
- Added some additional error handling.
- Added support for multi plants.

## 0.24

- Refactor of whole code
- Optimization of whole flow.
- webserver is disabled
- switch to read config from json
- changed sensor reset date to the begining of next day

## 0.23

- Correct "Missing default value for External_MQTT_TLS bug' - issue #44
- Try to solve issue #40 - 'dict object' has no attribute

## 0.22

- Correct - Option 'MQTT_HOST' does not exist in the schema for HoyMiles Solar Data Gateway Add-on
- Add device_class: power and state_class: measurement to real_power template
- TLS external server test
- Add timezone to last_data_time - issue #42

## 0.21

- External MQTT bug fix
- New sensors magnitude

### 0.20

"0.20i" - Support to the HA Energy Management dashboard (BETA)

- Change some sensors config (testing)
- Automatically receives login data from the mqqt server and ignores the config.
- Load HASS.IO MQTT host, user and pass
- Dark mode bug fix

### 0.19

"0.19" - amd64-base-python:3.9-alpine3.12 bug - now using 3.7-alpine3.12

### 0.18

"0.18" - fix returned a non-zero code on install
Alpine 3.13 bug - now using 3.12

### 0.17

Dockerfile error

### 0.16

- First webserver version
- Comum.py
- https://www.buymeacoffee.com/dmslabs
- Images

### 0.15

- Bug fix
- dic['expire_after'] error

### 0.14

- float2number fix

### 0.13

- Bug fix

### 0.12

- Realpower round
- Other data round and scale
- sensors update

### 0.11

- Bug fix

### 0.10

- MQTT_STATUS_CODE
- Sensor DIC
- More debug information
- dmslibs.PrintC

### 0.09

- bug fix pegaDadosSolar()
- fixed I can't get access token
- changed loop to get data

### 0.08

- DEVELOPERS_MODE logs
- Changer Network port in config.json

### 0.07

- Add DEVELOPERS_MODE at add-on config

### 0.06

- Power ratio \* 100;
- Expire interval = Get Data Interval \* 1.5
