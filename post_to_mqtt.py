from hbmqtt.client import MQTTClient, ConnectException
from bleson import get_provider, Observer
import os
import json_tricks
import asyncio
import sys

mqtt_url = os.environ.get("MQTT_URL", "mqtt://localhost/")
mqtt_topic = os.environ.get("MQTT_TOPIC", "/home/ble")

def bytes_to_string(obj):
    if isinstance(obj, bytes):
        return obj.decode('iso-8859-1')
    return obj

def advertisement_to_json(advertisement):
    return json_tricks.dumps(advertisement, extra_obj_encoders=[bytes_to_string], primitives=True)

client = MQTTClient()

def on_advertisement(advertisement):
    asyncio.ensure_future(client.publish(mqtt_topic, advertisement_to_json(advertisement).encode("utf-8")))

def start_listen_ble():
    try:
        adapter = get_provider().get_adapter()

        observer = Observer(adapter)
        observer.on_advertising_data = on_advertisement

        observer.start()
    except OSError:
        print("Error listening for BLE advertisements, using fixed test data instead")

        data = """{"svc_data_uuid16": null, "uri": null, "type": "ADV_IND", "adv_itvl": null, "svc_data_uuid32": null, "flags": 26, "address_type": "PUBLIC", "appearance": null, "svc_data_uuid128": null, "rssi": -53, "raw_data": null, "tx_pwr_lvl": null, "uuid128s": [{"_uuid_obj": {"int": 270829573007142736156654800289003511292}, "_uuid": "cbbfe0e1-f7f3-4206-84e0-84cbb3d09dfc"}], "uuid16s": [], "_name": null, "public_tgt_addr": null, "mfg_data": null, "address": {"address": "88:82:12:99:0F:D8"}, "name_is_complete": false, "uuid32s": [], "service_data": null}"""

        async def post_data(client):
            while True:
                try:
                    await client.publish(mqtt_topic, data.encode('utf-8'))
                except Exception as e:
                    # Can't really do anything, better luck next time
                    pass

                await asyncio.sleep(1)
        asyncio.ensure_future(post_data(client))

@asyncio.coroutine
def main():
    try:
        yield from client.connect(mqtt_url)
        print("Connected")
        start_listen_ble()
    except Exception as e:
        print("Connection failed: %s" % e)
        asyncio.get_event_loop().stop()

asyncio.ensure_future(main())
asyncio.get_event_loop().run_forever()
