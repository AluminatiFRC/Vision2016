import paho.mqtt.client as mqtt
import sys
import socket
import time

class MqttClient:
    def __init__(self, host, port, topics, messageHandler = None):#, userdata = None):
        self.__isConnected = False
        self.__host = host
        self.__port = port
        self.__topics = topics
        self.__pahoClient = mqtt.Client()
        self.__pahoClient.on_connect = self.on_connect
        self.__pahoClient.on_disconnect = self.on_disconnect
        self.__pahoClient.on_message = self.on_message
        #self.userdata = userdata
        self.messageHandler = messageHandler

    def connect(self):
        try:
            self.__pahoClient.loop_start()
            self.__pahoClient.connect(self.__host, self.__port)
        except socket.gaierror as error:
            print("Not able to resolve the requested host name: " + self.__host)
            raise
        except socket.error as error:
            if error.errno == socket.errno.ETIMEDOUT:
                print("Found host, but could not connect to it. (Maybe your port number is wrong.)")
            else:
                print("There was a problem connecting to the server.\n" + str(error))
            raise
        except:
            print "Unhandled error " + str(sys.exc_info()[0])
            raise

    def publish(self, topic, payload):
        self.__pahoClient.publish(topic, payload)    

    def isConnected(self):
        return self.__isConnected
    
    def disconnect(self):
        if self.__isConnected and self.__pahoClient != None:
            self.__pahoClient.disconnect()

    def on_connect(self, client, userdata, _, resultCode):
        print "Connected to MQTT broker with result code: " + str(resultCode)
        if resultCode == 0:
            self.__isConnected = True
            for topic in self.__topics:
                client.subscribe(topic)
        else:
            self.__isConnected = False
    
    def on_message(self, client, userdata, message):
        if self.messageHandler != None:
            self.messageHandler(message)#, self.userdata)

    def on_disconnect(self, client, userdata, resultCode):
        print("Disconnected from MQTT broker with result code " + str(resultCode))
        self.__isConnected = False

## Example Usage
def sampleCode():
    def messageHandler(message):
        sys.stdout.write(".")
        #print message.topic
        #print message.payload

    #host = "iot.eclipse.org"
    #port = 1883
    host = "roboRIO-5495-FRC.local"
    port = 5888
    topics = ("$SYS/#")
    client = MqttClient(host, port, topics, messageHandler)

    for i in range(5):
        time.sleep(1)
        print("\ntick\n")
        
    client.disconnect()

#sampleCode()
