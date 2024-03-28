import os
import web
import json
import paho.mqtt.client as mqtt
import uuid
import time
import threading
import serial.tools.list_ports
from RFLink import RFLink
from RFLinkMQTTListener import RFLinkMQTTListener
import queue
import subprocess   #to get paho-mqtt version
from packaging import version #to compare paho-mqtt version
from datetime import datetime # for mqtt message timestamp

app = web.application(urls, globals())
print("Outside if name == main")
if __name__ == "__main__":
    print("First line inside if name == main")
    # rflink = RFLink(rflink_settings)
    # rfLinkMQTTListener = RFLinkMQTTListener(rflink_settings["items"], rflink, mqtt_servers, use_paho_client_constructor_arg)
    # rfLinkMQTTListener.subscribe_mqtt()
    # print(f"rflink {rflink is not None}, serial: {rflink.serial is not None}, connected: {rflink.connected}, open: {rflink.serial.isOpen()}")
    # # print(f"rflink {get_rflink() is not None}, serial: {get_rflink().serial is not None}, connected: {get_rflink().connected}, open: {get_rflink().serial.isOpen()}")
    app.run()
    print("Last line inside if name == main")


