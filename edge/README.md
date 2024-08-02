# HoyMiles Solar Data Gateway Add-on Edge version

# Branch in full full development mode - will be rewritten from scratch

## Important Info

Addon is in maintenance mode. This is FOSS (Free Open Source Software) and based on reverse engineering so it could not work always as expected. What is more due to techical dept present implementation loose possibility to add new features. This mean that it **required rewriting from scratch**. Without support from community it **is not predicted soon**.

Br,
Cosik.

## Info

Development versions can be unstable.

Application to read Hoymiles Gateway Solar Data using unofficial API

I developed this program to integrate my solar system data to [Home Assistant](https://www.home-assistant.io/) Application through an add-on.

Now, [Cosik](https://github.com/Cosik)  is helping too.

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fdmslabsbr%2Fhoymiles)

But you can use the application without using the Home Assistant. You just need a machine that runs Python3. It based on mqtt messages, so could be send from any device to MQTT Broker.


Donate Cosik ->
[![Donate Cosik](https://img.shields.io/badge/Donate-PayPal-green.svg)](paypal.me/cosik3d)

<img alt="Lines of code" src="https://img.shields.io/tokei/lines/github/dmslabsbr/hoymiles">
<img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/dmslabsbr/hoymiles">


# Instructions

<img align="center" src="https://github.com/dmslabsbr/smsUps/raw/master/hass.io.png" alt="" width="30" /> [Home Assistant add-on instructions](DOCS.md)


Before run you need to install:
   https://github.com/eclipse/paho.mqtt.python  ***and***
   https://github.com/psf/requests


```bash
git clone https://github.com/dmslabsbr/hoymiles.git
cd hoymiles
python3 -m venv ./hoymiles/
source ./bin/activate
pip3 install paho-mqtt==1.6.1
pip3 install requests
pip3 install python-dateutil
```

My solar panels communicate with the internet using a DTU-W100 gateway.

<img src="https://github.com/dmslabsbr/hoymiles/raw/master/img/icon.png" alt="" width="300" />

But it will probably work with any device that uses the [global.hoymiles.com](https://global.hoymiles.com/) Website. It was tested with DTU-PRO also.


# Supported devies

So far it is confirmed that addon support Hoymiles devices:
- micro inverters
- standard inverters
- energy meters
- bms (with some restrictions)
- batteries (with some restrictions)
- multiple instalattions

## Restrictions

Addon support batteries and bms. Present is support only two modes:
- self consumption
- force charge

Due to technical dept there **is no feedback about enabled mode and set values.**


## PS:
I invite everyone to help in the this tool development.

## Screenshots

<img src="https://github.com/dmslabsbr/hoymiles/blob/master/edge/img/Hass1.png?raw=true" alt="" width="400" />

<img src="https://github.com/dmslabsbr/hoymiles/blob/master/edge/img/Hass2.png?raw=true" alt="" width="400" />

<img src="https://github.com/dmslabsbr/hoymiles/blob/master/edge/img/Hass3.png?raw=true" alt="" width="400" />



#### Licence

> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
