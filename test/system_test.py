import os
import subprocess
import post_to_mqtt
import pytest

import paho.mqtt.client as mqtt
import multiprocessing
import time
import json

TEST_TOPIC = "/test"
CONNECTION_WAIT_TOPIC = "/mqtt-test"
WAIT_SECONDS = 5

@pytest.mark.skipif(os.environ.get("HAVE_MQTT", None) is None, reason="Need MQTT environment")
def test_mqtt_posting(docker_image, mqtt_broker):
    hostname, port = mqtt_broker
    bridge = None

    connection_wait_messages = []
    received_messages = []
    def on_connect(client, userdata, flags, rc):
        print("Tester connected")
        client.subscribe(TEST_TOPIC)
        client.subscribe(CONNECTION_WAIT_TOPIC)

    def on_message(client, userdata, msg):
        if msg.topic == TEST_TOPIC:
            received_messages.append(msg)
        elif msg.topic == CONNECTION_WAIT_TOPIC:
            print("Tester received MQTT connection validation message")
            connection_wait_messages.append(msg)
        else:
            print("Received unexpected message", msg)
            
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.loop_start()
        client.connect(hostname, port, 60)

        for i in range(WAIT_SECONDS * 10):
            if connection_wait_messages:
                print("Tester got message through broker", connection_wait_messages[0])
                break
            print("Publishing connection wait message")
            client.publish(CONNECTION_WAIT_TOPIC, payload="foo")
            time.sleep(.1)
        else:
            pytest.fail("Tester could not pass message through broker")

        mqtt_url = "mqtt://mqtt:1883"
        cmd = ["docker", "run", "--rm", "--link", "test_vernemq:mqtt", "-e", "MQTT_TOPIC=" + TEST_TOPIC, "-e", "MQTT_URL=" + mqtt_url, docker_image, "test"]
        print(" ".join(cmd))
        bridge = multiprocessing.Process(target=lambda: subprocess.check_output(cmd), daemon=True)
        bridge.start()

        first_message_at = None
        for i in range(WAIT_SECONDS * 10):
            if len(received_messages) != 0:
                print("Got messages", received_messages)
                break
            time.sleep(.1)
        else:
            pytest.fail("Tester did not receive message from bridge")
    finally:
        client.loop_stop()
        if bridge is not None:
            bridge.terminate()

@pytest.fixture(scope="function")
def docker_image():
    import random
    n = random.randint(0, 10000)
    tag = "test-" + str(n)
    image = subprocess.check_output(["docker", "build", ".", "-t", tag])
    return tag

@pytest.fixture(scope="function")
def mqtt_broker(monkeypatch):
    vernemq_cmd = ["docker", "run", "--rm", "--name", "test_vernemq", "-e", "DOCKER_VERNEMQ_ALLOW_ANONYMOUS=on", "-e", "DOCKER_VERNEMQ_ACCEPT_EULA=yes", "-p", "1883", "vernemq/vernemq:1.12.3"]
    print(" ".join(vernemq_cmd))
    vernemq = multiprocessing.Process(target=lambda: subprocess.run(vernemq_cmd, check=True), daemon=True)
    vernemq.start()
    while not 'test_vernemq' in subprocess.check_output(["docker", "ps"]).decode("utf-8"):
        print("Tester waiting for VerneMQ to start")
        time.sleep(1)
    while not 'cluster event handler' in subprocess.check_output(["docker", "logs", "test_vernemq"]).decode("utf-8"):
        print("Tester waiting for VerneMQ to initialize")
        time.sleep(1)
        
    port = subprocess.check_output(["docker", "port", "test_vernemq", "1883"]).decode("utf-8").split("\n")[0].split(":")[1]
    yield "localhost", int(port)
    subprocess.run(["docker", "kill", "test_vernemq"])
    vernemq.terminate()
