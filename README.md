# Bridge BLE Advertisements to an MQTT topic

Designed for Raspberry Pi and Docker.

## Build the image for local testing on non-raspbian platforms

`docker build -t py-ble-mqtt-bridge --build-arg BASE_IMAGE=debian:stretch .`

## Build the image for Raspberry Pi

`docker build -t py-ble-mqtt-bridge`

## Run

`docker run -it -e MQTT_URL=mqtt://localhost/ -e MQTT_TOPIC=/home/ble py-ble-mqtt-bridge`

