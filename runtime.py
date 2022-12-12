"""Runtime MQTT client."""
import paho.mqtt.client as paho
import sys

broker = "192.168.1.154"
run = True


def on_message(client, userdata, msg):
    """Callback for receive msg."""
    print(msg.topic + ": " + msg.payload.decode())


def on_log(client, userdata, level, buf):
    """Callback for logging."""
    print("log: " + buf)


def on_connect(client, userdata, flags, rc):
    """Callback for connect to broker."""
    if rc == 0:
        print("connect OK")
    else:
        print("Could not connect to MQTT Broker!")


def on_disconnect(client, userdata, flags, rc=0):
    """Callback for disconnect from broker."""
    print("Disconnected return code " + str(rc))
    run = False


if __name__ == '__main__':
    client = paho.Client()
    client.will_set(
        "runtime/keepalive", payload="last will message!", qos=0, retain=False)
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log

    client.connect(broker, port=1883, keepalive=60)
    while run:
        client.loop()
