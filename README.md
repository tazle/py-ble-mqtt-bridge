# Bridge BLE Advertisements to an MQTT topic

Designed for Raspberry Pi and Docker.

## Build the image for local testing on non-raspbian platforms

`docker build -t py-ble-mqtt-bridge .`

## Build the image for Raspberry Pi

`docker build -t py-ble-mqtt-bridge`

## Run

`docker run -it -e MQTT_URL=mqtt://localhost/ -e MQTT_TOPIC=/home/ble py-ble-mqtt-bridge`

## Set up dev environment

```
python3 -m virtualenv venv -p $(which python3)
venv/bin/pip install -r requirements-dev.txt
venv/bin/pip install -r requirements.txt
```

## Test

`HAVE_MQTT=1 PYTHONPATH=$PWD venv/bin/py.test`
