<img src="https://github.com/dmslabsbr/hoymiles/raw/master/logo.png" alt="" width="200" />


# HoyMiles Solar Data Gateway Add-on
Application to read Hoymiles Gateway Solar Data

I developed this program to integrade my solar system data to the [Home Assistant](https://www.home-assistant.io/) Application through an add-on.

But you can use the application without using the Home Assistant. You just need a machine that runs Python3.

<a href="https://www.buymeacoffee.com/dmslabs"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a pizza&emoji=🍕&slug=dmslabs&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff"></a>

<form action="https://www.paypal.com/donate" method="post" target="_top">
<input type="hidden" name="hosted_button_id" value="9S3JYKPHR3XQ6" />
<input type="image" src="https://img.shields.io/badge/Donate-PayPal-green.svg" border="0" name="submit" title="PayPal - The safer, easier way to pay online!" alt="Donate with PayPal button" />
</form>

[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1MAC9RBnPYT9ua1zsgvhwfRoASTBKr4QL8)](https://www.blockchain.com/btc/address/1MAC9RBnPYT9ua1zsgvhwfRoASTBKr4QL8)

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
pip3 install paho-mqtt
pip3 install requests
```

My solar panels communicate with the internet using a DTU-W100 gateway.

<img src="https://github.com/dmslabsbr/hoymiles/raw/master/icon.png" alt="" width="300" />

But it will probably work with any device that uses the [global.hoymiles.com](https://global.hoymiles.com/) Website


## PS:
I invite everyone to help in the this tool development.

## Screenshots

<img src="https://github.com/dmslabsbr/hoymiles/raw/img/Hass1.png" alt="" />
<img src="https://github.com/dmslabsbr/hoymiles/raw/img/Hass2.png" alt="" />
<img src="https://github.com/dmslabsbr/hoymiles/raw/img/Hass3.png" alt="" />

