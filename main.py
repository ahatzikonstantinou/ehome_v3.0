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
import asyncio
import queue
import signal
import subprocess   #to get paho-mqtt version
from packaging import version #to compare paho-mqtt version
from datetime import datetime # for mqtt message timestamp


urls = (
    '/', 'Index',
    '/index', 'Index',
    '/settings', 'Settings',
    '/create/mqtt-server', 'CreateMqttServer',
    '/retrieve/mqtt-server/(\d+)', 'RetrieveMqttServer',
    '/update/mqtt-server/(\d+)', 'UpdateMqttServer',
    '/delete/mqtt-server/(\d+)', 'DeleteMqttServer',
    '/test/mqtt-server/(\d+)', 'TestMqttServerConnectivity',
    '/create/container', 'CreateContainer',
    '/retrieve/container/(\d+)', 'RetrieveContainer',
    '/update/container/(\d+)', 'UpdateContainer',
    '/delete/container/(\d+)', 'DeleteContainer',
    '/move/container/(\d+)/(up|down)', 'MoveContainer',
    '/create/item', 'CreateItem',
    '/retrieve/item/(\d+)', 'RetrieveItem',
    '/update/item/(\d+)', 'UpdateItem',
    '/delete/item/(\d+)', 'DeleteItem',
    '/move/item/(\d+)/(up|down)', 'MoveItem',
    '/rflink/activate', 'RFLinkActivate',
    '/rflink/deactivate', 'RFLinkDeactivate',
    '/rflink/debug/(\d)', 'RFLinkDebug',
    # '/rflink/sse', 'SSE',
    '/rflink_item', 'RFLinkItemIndex',
    '/rflink_item/create', 'RFLinkItemCreate',
    '/rflink_item/update/(\d+)', 'RFLinkItemUpdate',
    '/rflink_item/delete/(\d+)', 'RFLinkItemDelete',
    '/rflink_item/(\d+)/command/create', 'RFLinkItemCommandCreate',
    '/rflink_item/(\d+)/state/create', 'RFLinkItemStateCreate',
    '/rflink_item/(\d+)/command/(\d+)/delete', 'RFLinkItemCommandDelete',
    '/rflink_item/(\d+)/state/(\d+)/delete', 'RFLinkItemStateDelete',
    '/rflink_item/(\d+)/command/(\d+)/update', 'RFLinkItemCommandUpdate',
    '/rflink_item/(\d+)/state/(\d+)/update', 'RFLinkItemStateUpdate',
    '/rflink_item/(\d+)/command/(\d+)/add-exact', 'RFLinkItemCommandAddExact',
    '/rflink_item/(\d+)/state/(\d+)/add-exact', 'RFLinkItemStateAddExact',
    '/rflink_item/(\d+)/state/(\d+)/add-shift', 'RFLinkItemStateAddShift',
    '/rflink_item/(\d+)/command/(\d+)/delete-exact/(\d+)', 'RFLinkItemCommandDeleteExact',
    '/rflink_item/(\d+)/state/(\d+)/delete-exact/(\d+)', 'RFLinkItemStateDeleteExact',
    '/rflink_item/(\d+)/state/(\d+)/delete-shift/(\d+)', 'RFLinkItemStateDeleteShift',
    '/rflink_item/(\d+)/state/(\d+)/use-exact-pulse/(\d+)', 'RFLinkItemStateUseExactPulse',
    '/rflink_item/(\d+)/state/(\d+)/use-shift-window/(\d+)', 'RFLinkItemStateUseShiftWindow',
    '/rflink_item/(\d+)/state/(\d+)/shift-window-size/(\d+)', 'RFLinkItemStateShiftWindowSize',
    '/rflink_item/(\d+)/state/(\d+)/use-max-common-substring/(\d+)', 'RFLinkItemStateUseMaxCommonSubstring',
    '/rflink_item/(\d+)/state/(\d+)/pulse-middle', 'RFLinkItemStatePulseMiddle',
    '/rflink_item/test', 'RFLinkItemTest',
    '/language', 'SetLanguage',
    '/healthcheck', 'HealthCheck'
)

# Create a directory named 'data' if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# File path for mqtt-servers.json
mqtt_servers_file_path = os.path.join('data', 'mqtt-servers.json')

# Load MQTT servers from JSON file or create an empty list if file doesn't exist
if os.path.exists(mqtt_servers_file_path):
    with open(mqtt_servers_file_path, 'r') as f:
        mqtt_servers = json.load(f)
else:
    mqtt_servers = []

# File path for containers.json
containers_file_path = os.path.join('data', 'containers.json')

# Load containers from JSON file or create an empty list if file doesn't exist
if os.path.exists(containers_file_path):
    with open(containers_file_path, 'r') as f:
        containers = json.load(f)
else:
    containers = []

# File path for items.json
items_file_path = os.path.join('data', 'items.json')

# Load items from JSON file or create an empty list if file doesn't exist
if os.path.exists(items_file_path):
    with open(items_file_path, 'r') as f:
        items = json.load(f)
else:
    items = []

# File path for rflink.json
rflink_file_path = os.path.join('data', 'rflink.json')

# Load rflink from JSON file or create an empty list if file doesn't exist
if os.path.exists(rflink_file_path):
    with open(rflink_file_path, 'r') as f:
        rflink_settings = json.load(f)
        #remove duplicate pulses
        for rfi in rflink_settings["items"]:
            for c in rfi["commands"]:
                c["pulses_exact"] = list(set(c["pulses_exact"]))
            for s in rfi["states"]:
                s["pulses_exact"] = list(set(s["pulses_exact"]))
                s["pulses_shift"] = list(set(s["pulses_shift"]))
    with open(rflink_file_path, 'w') as f:
            json.dump(rflink_settings, f, indent=4)

else:
    rflink_settings = {"activated": False, "debug": False, "serial_port": "COM1", "items": []}

# File path for settings.json
settings_file_path = os.path.join('data', 'settings.json')

# Load settings from JSON file or create an empty list if file doesn't exist
if os.path.exists(settings_file_path):
    with open(settings_file_path, 'r') as f:
        settings = json.load(f)
else:
    settings = {"language": "el"}

domains = ["LIGHT", "DOOR", "WINDOW", "CLIMATE", "CAMERA"]

item_types = [
    { "id":"ALARM", "description": "Alarm"}, 
    { "id":"SMS", "description": "Sms" },
    { "id":"MODEM", "description": "Modem"}, 
    { "id":"DOOR1", "description": "Door single"}, 
    { "id":"DOOR1R", "description": "Door reclining single"}, 
    { "id":"DOOR2R", "description": "Door reclining double"}, 
    { "id":"WINDOW1", "description": "Window single"},
    { "id":"WINDOW1R", "description": "Window reclining single"}, 
    { "id":"WINDOW2R", "description": "Window reclining double"}, 
    { "id":"NET", "description": "Net"}, 
    { "id":"ROLLER1_AUTO", "description": "Roller auto single"}, 
    { "id":"ROLLER1", "description": "Roller single"}, 
    { "id":"LIGHT", "description": "LIGHT"}, 
    { "id":"LIGHT1", "description": "Light single"}, 
    { "id":"LIGHT2", "description": "Light double"}, 
    { "id":"TEMPERATURE_HUMIDITY", "description": "Temperature - Humidity"}, 
    { "id":"IPCAMERAPANTILT", "description": "IP Camera pan-tilt"}, 
    { "id":"MOTIONCAMERAPANTILT", "description": "Motion Camera pan-tilt"}, 
    { "id":"IPCAMERA", "description": "IP Camera"}, 
    { "id":"MOTIONCAMERA", "description": "Motion Camera"},
    { "id":"MOTIONSENSOR", "description": "Motion sensor"},
    { "id":"WATERTANK", "description": "Water tank"},
]
 
render = web.template.render('templates/', base='menu')
# render = web.template.render('templates/')

def get_paho_mqtt_version():
    try:
        result = subprocess.check_output(['pip', 'show', 'paho-mqtt'])
        lines = result.decode('utf-8').split('\n')
        version_line = next((line for line in lines if line.startswith('Version: ')), None)
        if version_line:
            return version_line.split(' ')[1].strip()
    except subprocess.CalledProcessError:
        pass
    return None

paho_mqtt_version = get_paho_mqtt_version()
break_paho_mqtt_version = "2.0.0"
use_paho_client_constructor_arg = version.parse(paho_mqtt_version) >= version.parse(break_paho_mqtt_version)
print(f"paho_mqtt_version: {paho_mqtt_version} (:{version.parse(paho_mqtt_version)}), break_paho_mqtt_version:{break_paho_mqtt_version} (:{version.parse(break_paho_mqtt_version)}), use_paho_client_constructor_arg: {use_paho_client_constructor_arg}")

def publish_mqtt(server, topic, data):
    
    try:
        client = None
        if use_paho_client_constructor_arg:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        else:
            client = mqtt.Client()
        client.connect(host=server['address'], port=int(server['port']))
        client.publish(topic, data, retain=True)
        client.disconnect()
        print(f"Published topic: {topic}, message: {data}, successfully to {server['address']}")
    except Exception as e:
        print(f"Failed to connect to {server['address']}: {e}")

class Messenger:
    RFLinkLinesMqttTopic = "RFLinkLines"
    def __init__(self):
        print(f"Messenger starting.")
        self.statesQueue = queue.Queue()
        self.linesQueue = queue.Queue()
        thread = threading.Thread(target=self.publish_thread)
        thread.daemon = True  # Daemonize the thread so it exits when the main program exits
        thread.start()

    def SendData(self):
        # Causes the program to hang, needs fixing
        print("Set to send data.")
        # thread = threading.Thread(target=self.publish_settings_thread)
        # thread.daemon = True  # Daemonize the thread so it exits when the main program exits
        # thread.start()
    
    def SendStates(self, detectedStates):
        self.statesQueue.put(detectedStates)
        print(f"Set to send {len(detectedStates)} states")

    def SendLine(self, line):
        self.linesQueue.put(line)
        print(f"Set to send {line} states")

    def publish_thread(self):
        while True:
            #publish detected states
            while not self.statesQueue.empty():
                detectedStates = self.statesQueue.get()
                timestamp = datetime.now()
                formatted_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                for ds in detectedStates:
                    publish_mqtt(
                        mqtt_servers[ds.rflink_item["mqtt_server"]],
                        ds.rflink_item["mqtt_state_publish_topic"], 
                        f"{{{ds.state_name} , \"timestamp\" : \"{formatted_timestamp}\"}}"
                    )

            #publish lines
            while not self.linesQueue.empty():
                line = self.linesQueue.get()
                # the settings page that will listens to the RFLinkLines topic
                # subscribes to the first of mqtt servers
                publish_mqtt(
                    mqtt_servers[0],
                    Messenger.RFLinkLinesMqttTopic,
                    line
                )
            
            time.sleep(0.1)  # Sleep if the statesQueue is empty

    def publish_settings_thread(self):
        data = {
            'mqtt_servers': mqtt_servers,
            'containers': containers,
            'item_types': item_types,
            'items': items
        }
        for server in mqtt_servers:
            publish_mqtt(server, "test/topic", json.dumps(data, indent=4))

class Index:
    def GET(self):
        return render.index(
            mqtt_servers=mqtt_servers, 
            containers=containers, 
            domains=domains, 
            item_types=item_types, 
            items=items, 
            language=settings["language"])

ports = serial.tools.list_ports.comports()
serial_ports = []
# split each serial port object so I can get its full name
for port, desc, hwid in sorted(ports):
    # print(f"Port: {port}, Description: {desc}, Hardware ID: {hwid}")
    serial_ports.append(port)
    
class Settings:
    def GET(self):
        data = web.input(rflink_item_index=None, showSection="mqtt")
        # print("Sending mqtt_servers: {}".format(json.dumps(mqtt_servers, indent=4)))
        
        return render.settings(
            mqtt_servers=mqtt_servers, 
            containers=containers, 
            domains=domains, 
            item_types=sorted(item_types, key=lambda x: x["description"]), 
            items=items, 
            serial_ports = serial_ports, 
            rflink = { "connected" : rflink.connected, "error" : rflink.connection_error, "debug": rflink_settings["debug"] }, 
            rflink_items = rflink_settings["items"], 
            rflink_item_index = data.rflink_item_index, 
            language=settings["language"],
            RFLinkLinesMqttTopic = Messenger.RFLinkLinesMqttTopic,
            showSection=data.showSection)

class CreateMqttServer:
    def POST(self):
        data = web.input()
        address = data.get('address')
        port = data.get('port')
        ws_port = data.get('ws_port')
        username = data.get('username')
        password = data.get('password')
        
        mqtt_servers.append({
            'address': address,
            'port': port,
            'ws_port': ws_port,
            'username': username,
            'password': password
        })
        
        with open(mqtt_servers_file_path, 'w') as f:
            json.dump(mqtt_servers, f, indent=4)
        messenger.SendData()
        raise web.seeother('/settings?showSection=mqtt')

class RetrieveMqttServer:
    def GET(self, server_id):
        server_id = int(server_id)
        if server_id < len(mqtt_servers):
            return json.dumps(mqtt_servers[server_id])
        else:
            return json.dumps({"error": "Server not found"})

class UpdateMqttServer:
    def POST(self, server_id):
        server_id = int(server_id)
        print("Updating server {}".format(server_id))
        if server_id < len(mqtt_servers):
            data = web.input()
            mqtt_servers[server_id]['address'] = data.get('address')
            mqtt_servers[server_id]['port'] = data.get('port')
            mqtt_servers[server_id]['ws_port'] = data.get('ws_port')
            mqtt_servers[server_id]['username'] = data.get('username')
            mqtt_servers[server_id]['password'] = data.get('password')
            
            with open(mqtt_servers_file_path, 'w') as f:
                json.dump(mqtt_servers, f, indent=4)
            messenger.SendData()
            raise web.seeother('/settings?showSection=mqtt')
        else:
            return json.dumps({"error": "Server not found"})

class DeleteMqttServer:
    def POST(self, server_id):
        server_id = int(server_id)
        if server_id < len(mqtt_servers):
            if next((c for c in containers if c['mqttServer'] == server_id ), None) or next((i for i in items if i['itemMqttServer'] == server_id), None):
                return json.dumps({"error": "Server is used by container(s) and/or item(s)"})

            del mqtt_servers[server_id]
            
            with open(mqtt_servers_file_path, 'w') as f:
                json.dump(mqtt_servers, f, indent=4)
            messenger.SendData()
            raise web.seeother('/settings?showSection=mqtt')
        else:
            return json.dumps({"error": "Server not found"})

class TestMqttServerConnectivity:
    def POST(self, server_id):
        server_id = int(server_id)
        if server_id < len(mqtt_servers):
            server = mqtt_servers[server_id]
            client = mqtt.Client()
            try:
                client.connect(server['address'], int(server['port']))
                return json.dumps({"success": True})
            except Exception as e:
                return json.dumps({"error": str(e)})
        else:
            return json.dumps({"error": "Server not found"})

class CreateContainer:
    def POST(self):
        data = web.input()
        print('Received: {}'.format(json.dumps(data, indent=4))) 
        containerName = data.get('containerName')
        parentContainer = data.get('parentContainer')
        guid = str(uuid.uuid4())
        containers.append({
            'containerName': containerName,
            'parentContainer': None if not parentContainer else parentContainer,
            'guid': guid
        })
        
        with open(containers_file_path, 'w') as f:
            json.dump(containers, f, indent=4)
        messenger.SendData()
        raise web.seeother('/settings?showSection=containers')

class UpdateContainer:
    def POST(self, container_id):
        container_id = int(container_id)
        print("Updating container {}".format(container_id))
        if container_id < len(containers):
            data = web.input()
            print('Received: {}'.format(json.dumps(data, indent=4))) 
            containers[container_id]['containerName'] = data.get('containerName')
            containers[container_id]['parentContainer'] = None if not  data.get('parentContainer') else data.get('parentContainer')
            
            with open(containers_file_path, 'w') as f:
                json.dump(containers, f, indent=4)
            messenger.SendData()
            raise web.seeother('/settings?showSection=containers')
        else:
            return json.dumps({"error": "Container not found"})

class DeleteContainer:
    def POST(self, container_id):
        container_id = int(container_id)
        if container_id < len(containers):
            if containers[container_id]['parentContainer'] is None and next((i for i in items if i['itemContainer'] == containers[container_id]['guid']), None):
                return json.dumps({"error": "Container cannot be deleted because it has items but no parent."})
            
            for container in containers:
                if container['parentContainer'] == containers[container_id]['guid']:
                    container['parentContainer'] = containers[container_id]['parentContainer']
                    print("updating {}'s parent to {}".format(container['containerName'], containers[container_id]['parentContainer']))

            for item in items:
                if item['itemContainer'] == containers[container_id]['guid']:
                    item['itemContainer'] = containers[container_id]['parentContainer']
                    print("updating {}'s container to {}".format(item['itemName'], containers[container_id]['parentContainer']))

            del containers[container_id]
            
            with open(containers_file_path, 'w') as f:
                json.dump(containers, f, indent=4)
            messenger.SendData()
            raise web.seeother('/settings?showSection=containers')
        else:
            return json.dumps({"error": "Container not found"})

class MoveContainer:
    def POST(self, container_id, direction):
        container_id = int(container_id)
        if container_id > len(containers):
            raise Exception(f"Invalid container id {container_id}. Only {len(containers)} exist.")
        direction = direction
        if direction != "up" and direction != "down":
            raise Exception(f"Invalid direction {direction}. Valid values are 'up' and 'down'.")
        print(f"Moving {containers[container_id]['containerName']}({container_id}) {direction}.")
        candidate_swap_id = None
        length = len(containers)
        if direction == "up":
            for i in range(length):

                # iterated the list until container_id's position 
                if i == container_id:

                    # if a sibling exists before this container, swap
                    if i == container_id and candidate_swap_id is not None:  
                        containers[candidate_swap_id], containers[container_id] = containers[container_id], containers[candidate_swap_id]
                        with open(containers_file_path, 'w') as f:
                            json.dump(containers, f, indent=4)
                    
                    break; # nothing else to do
                else:   # we are not at container_id's position yet
                    # found an container_id's sibling before container_id, this is a candidate swap
                    if containers[i]["parentContainer"] == containers[container_id]["parentContainer"]:
                        candidate_swap_id = i
        elif direction == "down":
            for i in range(length - 1, -1, -1):
                # iterated the list until container_id's position 
                if i == container_id:

                    # if a sibling exists before this container, swap
                    if i == container_id and candidate_swap_id is not None:  
                        containers[candidate_swap_id], containers[container_id] = containers[container_id], containers[candidate_swap_id]
                        with open(containers_file_path, 'w') as f:
                            json.dump(containers, f, indent=4)
                    
                    break; # nothing else to do
                else:   # we are not at container_id's position yet
                    # found an container_id's sibling before container_id, this is a candidate swap
                    if containers[i]["parentContainer"] == containers[container_id]["parentContainer"]:
                        candidate_swap_id = i
        raise web.seeother('/settings?showSection=containers')

class CreateItem:
    def POST(self):
        data = web.input()
        print('Received: {}'.format(json.dumps(data, indent=4))) 
        itemName = data.get('itemName')
        itemMqttServer = int(data.get('itemMqttServer'))
        itemContainer = data.get('itemContainer')
        itemType = data.get('itemType')
        publish = data.get('publish')
        subscribe = data.get('subscribe')
        filterById = 'filterById' in data
        idFilterValue = data.get('idFilterValue')

        items.append({
            'itemName': itemName,
            'itemMqttServer': int(itemMqttServer),
            'itemContainer': itemContainer,
            'itemType': itemType,
            'publish': publish,
            'subscribe': subscribe,
            'filterById': filterById,
            'idFilterValue': idFilterValue
        })
        
        with open(items_file_path, 'w') as f:
            json.dump(items, f, indent=4)
        messenger.SendData()
        raise web.seeother('/settings?showSection=items')

class UpdateItem:
    def POST(self, item_id):
        item_id = int(item_id)
        print("Updating item {}".format(item_id))
        if item_id < len(items):
            data = web.input()
            print('Received: {}'.format(json.dumps(data, indent=4))) 
            items[item_id]['itemName'] = data.get('itemName')
            items[item_id]['itemMqttServer'] = int(data.get('itemMqttServer'))
            items[item_id]['itemContainer'] = data.get('itemContainer')
            items[item_id]['itemType'] = data.get('itemType')
            items[item_id]['publish'] = data.get('publish')
            items[item_id]['subscribe'] = data.get('subscribe')
            items[item_id]['filterById'] = 'filterById' in data
            items[item_id]['idFilterValue'] = data.get('idFilterValue')
            
            with open(items_file_path, 'w') as f:
                json.dump(items, f, indent=4)
            messenger.SendData()
            raise web.seeother('/settings?showSection=items')
        else:
            return json.dumps({"error": "Item not found"})

class DeleteItem:
    def POST(self, item_id):
        item_id = int(item_id)
        if item_id < len(items):
            del items[item_id]
            
            with open(items_file_path, 'w') as f:
                json.dump(items, f, indent=4)
            messenger.SendData()
            raise web.seeother('/settings?showSection=items')
        else:
            return json.dumps({"error": "Item not found"})
        
class MoveItem:
    def POST(self, item_id, direction):
        item_id = int(item_id)
        if item_id > len(items):
            raise Exception(f"Invalid item id {item_id}. Only {len(items)} exist.")
        direction = direction
        if direction != "up" and direction != "down":
            raise Exception(f"Invalid direction {direction}. Valid values are 'up' and 'down'.")
        print(f"Moving {items[item_id]['itemName']}({item_id}) {direction}.")
        candidate_swap_id = None
        length = len(items)
        if direction == "up":
            for i in range(length):

                # iterated the list until item_id's position 
                if i == item_id:

                    # if a sibling exists before this item, swap
                    if i == item_id and candidate_swap_id is not None:  
                        items[candidate_swap_id], items[item_id] = items[item_id], items[candidate_swap_id]
                        with open(items_file_path, 'w') as f:
                            json.dump(items, f, indent=4)
                    
                    break; # nothing else to do
                else:   # we are not at item_id's position yet
                    # found an item_id's sibling before item_id, this is a candidate swap
                    if items[i]["itemContainer"] == items[item_id]["itemContainer"]:
                        candidate_swap_id = i
        elif direction == "down":
            for i in range(length - 1, -1, -1):
                # iterated the list until item_id's position 
                if i == item_id:

                    # if a sibling exists before this item, swap
                    if i == item_id and candidate_swap_id is not None:  
                        items[candidate_swap_id], items[item_id] = items[item_id], items[candidate_swap_id]
                        with open(items_file_path, 'w') as f:
                            json.dump(items, f, indent=4)
                    
                    break; # nothing else to do
                else:   # we are not at item_id's position yet
                    # found an item_id's sibling before item_id, this is a candidate swap
                    if items[i]["itemContainer"] == items[item_id]["itemContainer"]:
                        candidate_swap_id = i
        raise web.seeother('/settings?showSection=items')

class RFLinkActivate:
    def POST(self):
        data = web.input()
        try:
            rflink_settings["activated"] = True
            rflink_settings["serial_port"] = data.get("serial_port")
            print(f"serial port: {rflink_settings['serial_port']}")
            rflink.connect(rflink_settings["serial_port"])
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        except Exception as e:
            print(f"Could not connect to serial port {rflink_settings['serial_port']}. Error: {e}")
            return json.dumps({"error": str(e)})
        raise web.seeother('/settings?showSection=rflink,pulses')

class RFLinkDeactivate:
    def POST(self):
        try:
            rflink.disconnect()
            rflink_settings["activated"] = False
            with open(rflink_file_path, 'w') as f:
                    json.dump(rflink_settings, f, indent=4)
        except Exception as e:
            print(f"Could not deactivate serial port {rflink_settings['serial_port']}. Error: {e}")
            return json.dumps({"error": str(e)})
        raise web.seeother('/settings?showSection=rflink,pulses')

class RFLinkDebug:
    def POST(self, debug):
        debug = int(debug)
        try:
            rflink_settings["debug"] = False if debug == 0 else True
            if rflink.connected:
                rflink.disconnect()
                rflink.rflink_settings = rflink_settings
                rflink.connect(rflink_settings["serial_port"])
            with open(rflink_file_path, 'w') as f:
                    json.dump(rflink_settings, f, indent=4)
        except Exception as e:
            print(f"Could not set debug of serial port {rflink_settings['serial_port']} to {debug}. Error: {e}")
            return json.dumps({"error": str(e)})
        raise web.seeother('/settings?showSection=rflink,pulses')

# rejected. No matter what, if the browser refreshes a few (10) times, the web app hangs
# because of the "while True" that is necessary to continually read the serial
# class SSE:
#     def GET(self):
#         web.header('Content-Type', 'text/event-stream')
#         web.header('Cache-Control', 'no-cache')

#         # Set keep-alive timeout to 30 seconds
#         web.header('Cache-Control', 'no-cache')
#         web.header('Connection', 'keep-alive')
#         web.header('Keep-Alive', 'timeout=30')

#         # Send initial data immediately to establish connection
#         yield 'data:Initial message\n\n'

#         # i = 0
#         while True:
#             lines = []
#             try:
#                 while True:
#                     line = rflink.readline()
#                     print(f"SSE read a line")
#                     if not line or len(line.strip()) == 0:
#                         break;
#                     else:
#                         lines.append(line.strip())
#             except Exception as e:
#                 print(f"Error reading from serial port: {e}")

#             for data in lines:                
#                 # 1. have rflink detect of this is a known state
#                 # remove the sequence id that rflink prefixes each line with
#                 line = ';'.join(data.split(';')[2:])
#                 print(f"Will try line: {line}")
#                 if len(line.strip()) == 0:
#                     print(f"Empty line")
#                     continue
#                 messenger.SendStates(rflink.detectStates(line))

#                 # 2. Send the recieved data to the settings web page via Server-Sent-Event
#                 yield f"data: {data}\n\n\n" #3 \n here to display correctly in textarea
            
#             time.sleep(1) #sleep is necessary in order to not block the app

class RFLinkItemIndex:
    def GET(self):
        return render.index(items)

class RFLinkItemCreate:
    def POST(self):
        data = web.input()
        print(f"rflink_item: {json.dumps(data, indent=4)}")
        guid = str(uuid.uuid4())
        rflink_item_name = data.get("name")
        rflink_item_mqtt_server = int(data.get("mqtt_server"))
        rflink_item_mqtt_state_publish_topic = data.get("mqtt_state_publish_topic")
        rflink_item_mqtt_command_subscribe_topic = data.get("mqtt_command_subscribe_topic")
        rflink_item_commands = []
        rflink_item_states = []
        rflink_settings["items"].append({
            "guid": guid,
            "name": rflink_item_name,
            "mqtt_server": rflink_item_mqtt_server,
            "mqtt_state_publish_topic": rflink_item_mqtt_state_publish_topic,
            "mqtt_command_subscribe_topic": rflink_item_mqtt_command_subscribe_topic,
            "commands": rflink_item_commands,
            "states": rflink_item_states
        })

        with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?rflink_item_index=' + str(len(rflink_settings["items"])) + '&showSection=rflink,item')
        #raise web.seeother('/settings?showSection=rflink,item')

class RFLinkItemUpdate:
    def POST(self, item_id):
        item_id = int(item_id)
        data = web.input()
        if item_id < len(rflink_settings["items"]):
            rflink_item_name = data.get("name")
            rflink_item_mqtt_server = int(data.get("mqtt_server"))
            rflink_item_mqtt_state_publish_topic = data.get("mqtt_state_publish_topic")
            rflink_item_mqtt_command_subscribe_topic = data.get("mqtt_command_subscribe_topic")
            rflink_settings["items"][item_id]["name"] = rflink_item_name
            rflink_settings["items"][item_id]["mqtt_server"] = rflink_item_mqtt_server
            rflink_settings["items"][item_id]["mqtt_state_publish_topic"] = rflink_item_mqtt_state_publish_topic
            rflink_settings["items"][item_id]["mqtt_command_subscribe_topic"] = rflink_item_mqtt_command_subscribe_topic
            with open(rflink_file_path, 'w') as f:
                    json.dump(rflink_settings, f, indent=4)
            raise web.seeother('/settings?rflink_item_index=' + str(item_id) + '&showSection=rflink,item')

class RFLinkItemDelete:
    def POST(self, item_id):
        item_id = int(item_id)
        if item_id < len(rflink_settings["items"]):
            del rflink_settings["items"][item_id]
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?showSection=rflink,item')

class RFLinkItemCommandCreate:
    def POST(self, item_id):
        item_id = int(item_id)
        data = web.input()
        if item_id < len(rflink_settings["items"]):
            rflink_settings["items"][item_id]["commands"].append({
                "name": data.get("rflink_item_command"),
                "pulses_exact":[],
                "pulse_middle": None
            })
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?rflink_item_index=' + str(item_id) + '&showSection=rflink,item')
    
class RFLinkItemStateCreate:
    def POST(self, item_id):
        item_id = int(item_id)
        data = web.input()
        if item_id < len(rflink_settings["items"]):
            rflink_settings["items"][item_id]["states"].append({
                "name": data.get("rflink_item_state"),
                "pulses_exact": [],
                "use_exact_pulse": True,
                "pulses_shift": [],
                "use_shift_window": True,
                "shift_window_size": 0,
                "use_max_common_substring": True,
                "max_common_substring": None,
                "pulse_middle": None
            })
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?rflink_item_index=' + str(item_id) + '&showSection=rflink,item')

class RFLinkItemCommandUpdate:
    def POST(self, itemd_id, command_id):
        item_id = int(item_id)
        command_id = int(command_id)
        if item_id < len(rflink_settings["items"]) and command_id < len(rflink_settings["items"][item_id]["commands"]) :
            rflink_settings["items"][item_id]["commands"][command_id]["name"] = web.input().get("rflink_item_command")
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?rflink_item_index=' + str(item_id) + '&showSection=rflink,item')
        
class RFLinkItemStateUpdate:
    def POST(self, item_id, state_id):
        item_id = int(item_id)
        state_id = int(state_id)
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]) :
            rflink_settings["items"][item_id]["states"][state_id]["name"] = web.input().get("rflink_item_state")
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?rflink_item_index=' + str(item_id) + '&showSection=rflink,item')
        
class RFLinkItemCommandDelete:
    def POST(self, item_id, command_id):
        item_id = int(item_id)
        command_id = int(command_id)
        if item_id < len(rflink_settings["items"]) and command_id < len(rflink_settings["items"][item_id]["commands"]) :
            del rflink_settings["items"][item_id]["commands"][command_id]
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?rflink_item_index=' + str(item_id) + '&showSection=rflink,item')

class RFLinkItemStateDelete:
    def POST(self, item_id, state_id):
        item_id = int(item_id)
        state_id = int(state_id)
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]) :
            del rflink_settings["items"][item_id]["states"][state_id]
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?rflink_item_index=' + str(item_id) + '&showSection=rflink,item')

class RFLinkItemCommandAddExact:
    def POST(self, item_id, command_id):
        item_id = int(item_id)
        command_id = int(command_id)
        if item_id < len(rflink_settings["items"]) and command_id < len(rflink_settings["items"][item_id]["commands"]) :
            # web.input does not work
            command = rflink_settings["items"][item_id]["commands"][command_id]
            postData = json.loads(web.data())
            data = postData['data']
            lines = data.split('\n')
            # print(f"item: {item_id}, command: {command_id}, pulseMiddle: {pulseMiddle}")
            for l in lines:
                if len(l.strip()) == 0:
                    print(f"Empty line")
                    continue
                pulse = rflink.processRawPulseLine(command['pulse_middle'], l).strip()
                if len(pulse) > 0 and pulse not in command['pulses_exact']:
                    command['pulses_exact'].append(pulse)
                else:
                    print(f"Pulse already in command {pulse}")
                
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)

            return json.dumps(command['pulses_exact'])

class RFLinkItemStateAddExact:
    def POST(self, item_id, state_id):
        item_id = int(item_id)
        state_id = int(state_id)
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]) :
            # web.input does not work
            state = rflink_settings["items"][item_id]["states"][state_id]
            postData = json.loads(web.data())
            data = postData['data']
            lines = data.split('\n')
            # print(f"item: {item_id}, state: {state_id}, pulseMiddle: {pulseMiddle}")
            for l in lines:
                if len(l.strip()) == 0:
                    print(f"Empty line")
                    continue
                pulse = rflink.processRawPulseLine(state['pulse_middle'], l).strip()
                if len(pulse) > 0 and pulse not in state['pulses_exact']:
                    state['pulses_exact'].append(pulse)
                else:
                    print(f"Pulse already in state exact {pulse}")
                
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)

            return json.dumps(state['pulses_exact'])

class RFLinkItemStateAddShift:
    def POST(self, item_id, state_id):
        item_id = int(item_id)
        state_id = int(state_id)
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]) :
            # web.input does not work
            state = rflink_settings["items"][item_id]["states"][state_id]
            postData = json.loads(web.data())
            data = postData['data']
            lines = data.split('\n')
            # print(f"item: {item_id}, state: {state_id}, pulseMiddle: {pulseMiddle}")
            for l in lines:
                if len(l.strip()) == 0:
                    print(f"Empty line")
                    continue
                if RFLink.RAW_PULSE_PATTERN not in l:   # silently reject non raw-pulse lines
                    continue
                pulse = rflink.processRawPulseLine(state['pulse_middle'], l).strip()
                if len(pulse) > 0 and pulse not in state['pulses_shift']:
                    state['pulses_shift'].append(pulse)
                else:
                    print(f"Pulse already in state shift {pulse}")
                    continue
            state["max_common_substring"] = rflink.getMaxCommonSubstring(state['pulses_shift'])   
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)

            return json.dumps({ "pulses_shift": state['pulses_shift'], "max_common_substring": state["max_common_substring"]})

class RFLinkItemCommandDeleteExact:
    def POST(self, item_id, command_id, pulse_sequence_id):
        item_id = int(item_id)
        command_id = int(command_id)
        pulse_sequence_id = int(pulse_sequence_id)
        if item_id < len(rflink_settings["items"]) and command_id < len(rflink_settings["items"][item_id]["commands"]) and pulse_sequence_id < len(rflink_settings["items"][item_id]["commands"][command_id]["pulses_exact"]) :
            state = rflink_settings["items"][item_id]["commands"][command_id]
            del state["pulses_exact"][pulse_sequence_id]
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)

            return json.dumps(state['pulses_exact'])

class RFLinkItemStateDeleteExact:
    def POST(self, item_id, state_id, pulse_sequence_id):
        item_id = int(item_id)
        state_id = int(state_id)
        pulse_sequence_id = int(pulse_sequence_id)
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]) and pulse_sequence_id < len(rflink_settings["items"][item_id]["states"][state_id]["pulses_exact"]) :
            state = rflink_settings["items"][item_id]["states"][state_id]
            del state["pulses_exact"][pulse_sequence_id]
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)

            return json.dumps(state['pulses_exact'])

class RFLinkItemStateDeleteShift:
    def POST(self, item_id, state_id, pulse_sequence_id):
        item_id = int(item_id)
        state_id = int(state_id)
        pulse_sequence_id = int(pulse_sequence_id)
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]) and pulse_sequence_id < len(rflink_settings["items"][item_id]["states"][state_id]["pulses_shift"]) :
            state = rflink_settings["items"][item_id]["states"][state_id]
            del state["pulses_shift"][pulse_sequence_id]
            state["max_common_substring"] = rflink.getMaxCommonSubstring(state['pulses_shift'])
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)

            return json.dumps({ "pulses_shift": state['pulses_shift'], "max_common_substring": state["max_common_substring"]})

class RFLinkItemStateUseExactPulse: 
    def POST(self, item_id, state_id, use):
        item_id = int(item_id)
        state_id = int(state_id)
        use = int(use) == 1
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]):
            rflink_settings["items"][item_id]["states"][state_id]["use_exact_pulse"] = use 
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
            return json.dumps({"success": True})
            
class RFLinkItemStateUseShiftWindow: 
    def POST(self, item_id, state_id, use):
        item_id = int(item_id)
        state_id = int(state_id)
        use = int(use) == 1
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]):
            rflink_settings["items"][item_id]["states"][state_id]["use_shift_window"] = use 
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
            return json.dumps({"success": True})
            
class RFLinkItemStateShiftWindowSize: 
    def POST(self, item_id, state_id, size):
        item_id = int(item_id)
        state_id = int(state_id)
        size = int(size)
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]):
            rflink_settings["items"][item_id]["states"][state_id]["shift_window_size"] = size 
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
            return json.dumps({"success": True})
            
class RFLinkItemStateUseMaxCommonSubstring: 
    def POST(self, item_id, state_id, use):
        item_id = int(item_id)
        state_id = int(state_id)
        use = int(use) == 1
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]):
            rflink_settings["items"][item_id]["states"][state_id]["use_max_common_substring"] = use 
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
            print(f"Returning ok")
            return json.dumps({"success": True})
        print(f"Returning nothing")
        
class RFLinkItemStatePulseMiddle: 
    def POST(self, item_id, state_id):
        item_id = int(item_id)
        state_id = int(state_id)
        if item_id < len(rflink_settings["items"]) and state_id < len(rflink_settings["items"][item_id]["states"]):
            pulseMiddle = int(json.loads(web.data())['pulseMiddle'])
            rflink_settings["items"][item_id]["states"][state_id]["pulse_middle"] = pulseMiddle 
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
            print(f"Returning ok")
            return json.dumps({"success": True})
        print(f"Returning nothing")
        
class RFLinkItemTest:
    def POST(self):
        data = json.loads(web.data())['data']
        lines = data.split('\n')
        print(f"Testing {len(lines)} lines")
        results = []
        for i,l in enumerate(lines):
            # remove the sequence id that rflink prefixes each line with
            l = ';'.join(l.split(';')[2:])
            print(f"Testing line {i}: {l}")
            if len(l.strip()) == 0:
                print(f"Empty line")
                continue
            results.append({ "line": l, "detection": rflink.detect(l, rflink_settings["items"]) })

            messenger.SendStates(rflink.detectStates(l))

        return json.dumps(results, indent=4)

class SetLanguage:
    def POST(self):
        settings["language"] = web.input().get("language")
        submitted_from_url = web.ctx.path
        print(f"submitted_from_url: {submitted_from_url}")
        with open(settings_file_path, 'w') as f:
            json.dump(settings, f, indent=4)
        return json.dumps({"success": True})

class HealthCheck:
    def GET(self):
        return "OK"
    
#autoreload=False is required to avoid double initialization see https://stackoverflow.com/a/42307911
app = web.application(urls, globals(), autoreload=False)

if __name__ == "__main__":    
    messenger = Messenger()
    rflink = RFLink(rflink_settings, messenger)
    rfLinkMQTTListener = RFLinkMQTTListener(
        rflink_settings["items"],
        rflink,
        mqtt_servers,
        use_paho_client_constructor_arg
    )
    rfLinkMQTTListener.subscribe_mqtt()
    app.run()
