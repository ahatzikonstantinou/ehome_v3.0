import paho.mqtt.client as mqtt
import json

class RFLinkMQTTListener:
    def __init__(self, rflink_items, rflink, mqtt_servers, use_paho_client_constructor_arg):
        self.rflink_items = rflink_items
        self.rflink = rflink
        self.mqtt_servers = mqtt_servers
        self.use_paho_client_constructor_arg = use_paho_client_constructor_arg
        self.mqtt_clients = {}
        
    def subscribe_mqtt(self):
        """
        Start listening for mqtt messages
        """
        for item in self.rflink_items:
            if item["mqtt_server"] > len(self.mqtt_servers):
                raise Exception("rflink item with guid {item['guid']} is using mqtt_server: {item['mqtt_server']} while the list of mqtt servers has ony {len(self.mqtt_servers)} elements.")
            if item["mqtt_server"] not in self.mqtt_clients:
                mqtt_server = self.mqtt_servers[item["mqtt_server"]]
                if self.use_paho_client_constructor_arg:
                    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
                else:
                    client = mqtt.Client()
                self.mqtt_clients[item["mqtt_server"]] = client
                client.connect(mqtt_server["address"], mqtt_server["port"])
                client.on_message = self.on_rflink_item_mqtt_message
                client.loop_start()

            topic = item[u"mqtt_command_subscribe_topic"]
            if topic:
                print("Subscribing to topic '{}'".format(topic))
                client.subscribe(topic, qos=2)

    def unsubscribe_mqtt(self):
        for c in self.mqtt_clients:
            c.loop_stop()
            c.close()

    def refresh_mqtt_subscriptions(self):
        self.unsubscribe_mqtt()
        self.subscribe_mqtt()    

    def on_rflink_item_mqtt_message(self, client, userdata, msg):
        """
        Callback when MQTT message is received from sensor
        """
        print(f"Received MQTT topic: {msg.topic} message: {msg.payload}")
        try:
            cmd = json.loads(msg.payload).get("command")
            print('MQTT cmd: {}'.format(cmd))
        except ValueError as e:
            print(u"RFLinkMQTTListener could not decode command: ", msg.payload, e)
            return
        items = [i for i in self.rflink_items if i["mqtt_command_subscribe_topic"] == msg.topic]
        for i in items:
            print(f"checking item guid {i['guid']}")
            if i['mqtt_command_subscribe_topic'] == msg.topic:
                for c in i["commands"]:
                    print(f"checking command {c['name']}")
                    if cmd in c['name']:
                        print(f"Will send rflink command {c['name'][cmd]}")
                        self.rflink.sendCommand(c['name'][cmd])

