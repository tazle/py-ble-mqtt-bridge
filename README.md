## Build image for local testing

`docker build -t py-ble-mqtt-bridge --build-arg BASE_IMAGE=debian:stretch .`

## Build image for Raspberry Pi

`docker build -t py-ble-mqtt-bridge`

## Run

`docker run -it -e MQTT_URL=mqtt://localhost/ -e MQTT_TOPIC=/home/ble py-ble-mqtt-bridge`
