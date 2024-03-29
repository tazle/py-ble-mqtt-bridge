from hbmqtt.client import MQTTClient, ConnectException
from bleson import get_provider, Observer
import os
import asyncio
import sys
import janus
import queue
import json
import pickle
from bleson.core.types import ValueObject, UUID16, UUID128, BDAddress
import time

mqtt_url = os.environ.get("MQTT_URL", "mqtt://localhost/")
mqtt_topic = os.environ.get("MQTT_TOPIC", "/home/ble")

loop = asyncio.get_event_loop()
_send_queue = janus.Queue(loop=loop, maxsize=5000)
ble_queue = _send_queue.sync_q
mqtt_queue = _send_queue.async_q

def bytes_to_string(obj):
    if isinstance(obj, bytes):
        return obj.decode('iso-8859-1')
    return obj

fields = ["svc_data_uuid32", "uuid16s", "tx_pwr_lvl", "name_is_complete", "uuid32s", "raw_data", "adv_itvl", "flags", "service_data", "rssi", "uuid128s", "appearance", "type", "svc_data_uuid16", "uri", "public_tgt_addr", "_name", "svc_data_uuid128", "address_type", "mfg_data", "address"]

class BlesonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return bytes_to_string(obj)
        if isinstance(obj, UUID16):
            return {"_uuid" : obj._uuid}
        if isinstance(obj, UUID128):
            return {"_uuid" : obj._uuid}
        if isinstance(obj, BDAddress):
            return {"address": obj.address}
        return json.JSONEncoder.default(self, obj)

def to_json(object, fields):
    result = {}
    for field in fields:
        value = getattr(object, field)
        result[field] = value
    return result

def advertisement_to_json(advertisement, receiver_mac):
    intermediate = to_json(advertisement, fields)
    intermediate['receiver_mac'] = receiver_mac
    return json.dumps(intermediate, cls=BlesonEncoder)

client = MQTTClient()

last_received_timestamp = time.time()
def on_advertisement(advertisement):
    global last_received_timestamp
    last_received_timestamp = time.time()
    try:
        payload = advertisement_to_json(advertisement, receiver_mac)
        ble_queue.put(payload)
    except queue.Full:
        print("Send queue full")
    except Exception as e:
        print("Some other error", e)

receiver_mac = None
def start_listen_ble():
    try:
        print("Initializing BLE support")
        adapter = get_provider().get_adapter()
        global receiver_mac
        receiver_mac = adapter.get_device_info().address.address

        observer = Observer(adapter)
        observer.on_advertising_data = on_advertisement

        print("Starting BLE receiver")
        observer.start()
    except OSError:
        print("Error listening for BLE advertisements, using fixed test data instead")

        start_send_test_data()

def start_send_test_data():
    print("Starting to send test data")
    data = """{"svc_data_uuid16": null, "uri": null, "type": "ADV_IND", "adv_itvl": null, "svc_data_uuid32": null, "flags": 26, "address_type": "PUBLIC", "appearance": null, "svc_data_uuid128": null, "rssi": -53, "raw_data": null, "tx_pwr_lvl": null, "uuid128s": [{"_uuid_obj": {"int": 270829573007142736156654800289003511292}, "_uuid": "cbbfe0e1-f7f3-4206-84e0-84cbb3d09dfc"}], "uuid16s": [], "_name": null, "public_tgt_addr": null, "mfg_data": null, "address": {"address": "88:82:12:99:0F:D8"}, "name_is_complete": false, "uuid32s": [], "service_data": null}"""
    async def generate_test_data():
        while True:
            await mqtt_queue.put(data)
            await asyncio.sleep(1)
    asyncio.ensure_future(generate_test_data())

BLE_RECEIVE_TIMEOUT = 15
MQTT_PUBLISH_TIMEOUT = 15

async def watchdog():
    print("Starting watchdog")
    while True:
        now = time.time()
        since_last_receive = (now - last_received_timestamp)
        since_last_publish = (now - last_publish_timestamp)

        if since_last_receive > BLE_RECEIVE_TIMEOUT:
            print("No new BT data in %d seconds, exiting" %BLE_RECEIVE_TIMEOUT)
            os._exit(1)
        if since_last_publish > MQTT_PUBLISH_TIMEOUT:
            print("Unable to publish to MQTT in %d seconds, exiting" %MQTT_PUBLISH_TIMEOUT)
            os._exit(2)

        await asyncio.sleep(1)

last_publish_timestamp = time.time()
async def post_data():
    global last_publish_timestamp
    print("Starting MQTT sender")
    while True:
        try:
            data = await mqtt_queue.get()
            await client.publish(mqtt_topic, data.encode('utf-8'))
            last_publish_timestamp = time.time()
        except Exception as e:
            print("Failed to publish", e)

OPERATIONAL="operational"
TEST="test"

async def main(mode=OPERATIONAL):
    try:
        print("Connecting")
        await client.connect(mqtt_url)
        print("Connected")
        if mode ==OPERATIONAL:
            start_listen_ble()
        else:
            start_send_test_data()
    except Exception as e:
        print("Connection failed: %s" % e)
        asyncio.get_event_loop().stop()

if __name__ == '__main__':
    chosen_mode = OPERATIONAL
    if "test" in sys.argv:
        chosen_mode = TEST
    asyncio.ensure_future(watchdog())
    asyncio.ensure_future(post_data())
    asyncio.ensure_future(main(chosen_mode))
    asyncio.get_event_loop().run_forever()
