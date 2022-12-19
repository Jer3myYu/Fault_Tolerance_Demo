"""Runtime MQTT client."""
import paho.mqtt.client as paho
import socket
import threading
import sys

# MQTT variables
broker = "192.168.1.251"

# UDP variables
msgFromServer = "Keepalive"
bytesToSend = str.encode(msgFromServer)
serverAddressPort = ("192.168.1.251", 15640)
bufferSize = 1024
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


def on_disconnect(client, userdata, rc=0):
    """Callback for disconnect from broker."""
    global run
    print("Disconnected return code " + str(rc))
    run = False


class keepalive(threading.Thread):
    """Thread for sending keepalive message."""

    def __init__(self, event, UDPClientSocket):
        threading.Thread.__init__(self)
        self.stopped = event
        self.UDPClientSocket = UDPClientSocket

    def run(self):
        """Override run function in keepalive thread class."""
        while not self.stopped.wait(10):
            try:
                self.UDPClientSocket.sendto(bytesToSend, serverAddressPort)
            except OSError:
                print("Network is down, stop sending keep")
                break


if __name__ == '__main__':
    # paho client setup
    client = paho.Client()
    client.will_set(
        "runtime/keepalive", payload="last will message!", qos=0, retain=False)
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log

    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # Run a thread for heartbeat messages
    stopFlag = threading.Event()
    heart_beat = keepalive(stopFlag, UDPClientSocket)
    heart_beat.daemon = True
    heart_beat.start()

    client.connect(broker, port=1883, keepalive=15)
    while run:
        client.loop()
    print("Network is down")
