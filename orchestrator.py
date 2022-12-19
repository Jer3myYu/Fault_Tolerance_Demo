"""Orchestrator MQTT client."""
import paho.mqtt.client as paho
import threading
import socket
import time
import sys

# MQTT variables
broker = "192.168.1.251"

# UDP variables
localIP = "192.168.1.251"
localPort = 15640
bufferSize = 1024

# Orchestrator variables
runtimes = {}
# create a lock
mutex = threading.Lock()


def on_message(client, userdata, msg):
    """Callback for receive msg."""
    global mutex
    global runtimes
    print(msg.topic + ": " + msg.payload.decode())
    if "last will" in msg.payload.decode():
        print("receive last will need more operation")


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
    print("Disconnected return code " + str(rc))


class listen(threading.Thread):
    """Thread for listening to client keepalive messages."""

    def __init__(self, UDPServerSocket):
        threading.Thread.__init__(self)
        self.UDPServerSocket = UDPServerSocket

    def run(self):
        """Override run function in keepalive thread class."""
        while True:
            try:
                bytesAddressPair = self.UDPServerSocket.recvfrom(bufferSize)
                message = bytesAddressPair[0]
                address = bytesAddressPair[1]
                clientMsg = "Message from Client:{}".format(message)
                clientIP = "Client IP Address:{}".format(address)
                print(clientMsg)
                print(clientIP)

                # record current time for checking keepalive
                mutex.acquire()
                if address in runtimes:
                    runtimes[address]['time'] = time.time()
                else:
                    runtimes[address] = {
                        'network': 'isAlive',
                        'runtime': 'isAlive',
                        'time': time.time()}
                mutex.release()
            except Exception as e:
                print("listening exception: {}".format(e))


class checkalive(threading.Thread):
    """Thread for frequently check alive status of runtimes."""

    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        """Override run function in checkalive thread class."""
        while not self.stopped.wait(15):
            mutex.acquire()
            now = time.time()
            for runtime in runtimes:
                if now - runtime['time'] > 30:
                    print("network of {} is dead".format(runtime))
                    runtimes[runtimes]['network'] = "dead"
                    print(runtimes)
            mutex.release()


if __name__ == '__main__':
    # paho client setup
    client = paho.Client()
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log

    # Create a datagram socket
    UDPServerSocket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM)
    # Bind to address and ip
    UDPServerSocket.bind((localIP, localPort))

    # Thread sponse the listening to UDP socket
    server = listen(UDPServerSocket)
    server.daemon = True
    server.start()

    # Thread sponce the check alive
    stopFlag = threading.Event()
    alive = checkalive(stopFlag)
    alive.daemon = True
    alive.start()

    client.connect(broker, port=1883, keepalive=60)
    client.subscribe("runtime/lastwill")
    client.loop_forever()
