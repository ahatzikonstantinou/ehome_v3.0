import os
import web
import json
import paho.mqtt.client as mqtt
import uuid
import time
import threading
import serial.tools.list_ports
from RFLink import RFLink
import asyncio
import websockets
import queue
import signal
import rflink_item

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
    '/create/item', 'CreateItem',
    '/retrieve/item/(\d+)', 'RetrieveItem',
    '/update/item/(\d+)', 'UpdateItem',
    '/delete/item/(\d+)', 'DeleteItem',
    '/rflink/activate', 'RFLinkActivate',
    '/rflink/deactivate', 'RFLinkDeactivate',
    '/rflink/debug/(\d)', 'RFLinkDebug',
    '/rflink/sse', 'SSE',
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
    '/rflink_item/(\d+)/state/(\d+)/add-exact', 'RFLinkItemStateAddExact',
    '/rflink_item/(\d+)/state/(\d+)/add-shift', 'RFLinkItemStateAddShift',
    '/rflink_item/(\d+)/state/(\d+)/delete-exact/(\d+)', 'RFLinkItemStateDeleteExact',
    '/rflink_item/(\d+)/state/(\d+)/delete-shift/(\d+)', 'RFLinkItemStateDeleteShift',
    '/rflink_item/(\d+)/state/(\d+)/use-exact-pulse/(\d+)', 'RFLinkItemStateUseExactPulse',
    '/rflink_item/(\d+)/state/(\d+)/use-shift-window/(\d+)', 'RFLinkItemStateUseShiftWindow',
    '/rflink_item/(\d+)/state/(\d+)/shift-window-size/(\d+)', 'RFLinkItemStateShiftWindowSize',
    '/rflink_item/(\d+)/state/(\d+)/use-max-common-substring/(\d+)', 'RFLinkItemStateUseMaxCommonSubstring',
    '/rflink_item/(\d+)/state/(\d+)/pulse-middle', 'RFLinkItemStatePulseMiddle',
    '/rflink_item/test', 'RFLinkItemTest'
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
else:
    rflink_settings = {"activated": False, "debug": False, "serial_port": "COM1", "items": []}

rflink = None
# For some unknown reason rflink is initialized twice
# which means that if the rflink_settings have activated = True
# there will be two attempts to open the serial port
# rflink = RFLink(rflink_settings). 
def get_rflink():
    global rflink
    if rflink is None:
        rflink = RFLink(rflink_settings)
    return rflink

domains = ["LIGHT", "DOOR", "WINDOW", "CLIMATE", "CAMERA"]

item_types = [
    { "id":"ALARM", "description": "Alarm"}, 
    { "id":"SMS", "description": "Sms" },
    { "id":"MODEM", "description": "Modem"}, 
    { "id":"DOOR1", "description": "Door single"}, 
    { "id":"DOOR1", "description": "Door reclining single"}, 
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
    { "id":"WATERTANK", "description": "Water tank"},
]
 
render = web.template.render('templates/')

def publish_mqtt(server, data):
    client = mqtt.Client()
    try:
        client.connect(host=server['address'], port=int(server['port']))
        client.publish("test/topic", data)
        client.disconnect()
        print(f"Published message successfully to {server['address']}")
    except Exception as e:
        print(f"Failed to connect to {server['address']}: {e}")

class Messenger:
    def __init__(self):
        self.i = 0
        
    def SendData(self):
        print("Set to send data.")
        thread = threading.Thread(target=self.publish_mqtt_thread)
        thread.start()

    def publish_mqtt_thread(self):
        data = {
            'mqtt_servers': mqtt_servers,
            'containers': containers,
            'item_types': item_types,
            'items': items
        }
        for server in mqtt_servers:
            publish_mqtt(server, json.dumps(data, indent=4))
        self.i = (self.i + 1) % 100


messenger = Messenger()

class Index:
    def GET(self):
        return render.index(mqtt_servers=mqtt_servers, containers=containers, domains=domains, item_types=item_types, items=items)

class Settings:
    def GET(self):
        data = web.input(rflink_item_index=None, showSection="mqtt")
        # print("Sending mqtt_servers: {}".format(json.dumps(mqtt_servers, indent=4)))
        return render.settings(
            mqtt_servers=mqtt_servers, 
            containers=containers, 
            domains=domains, 
            item_types=item_types, 
            items=items, 
            serial_ports = serial.tools.list_ports.comports(), 
            rflink = { "connected" : get_rflink().connected, "error" : get_rflink().connection_error, "debug": rflink_settings["debug"] }, 
            rflink_items = rflink_settings["items"], 
            rflink_item_index = data.rflink_item_index,
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

class CreateItem:
    def POST(self):
        data = web.input()
        print('Received: {}'.format(json.dumps(data, indent=4))) 
        itemName = data.get('itemName')
        itemMqttServer = data.get('itemMqttServer')
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
            items[item_id]['itemMqttServer'] = data.get('itemMqttServer')
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
    def POST(self, item_id):
        if item_id > len(items):
            return
        data = web.input()
        print(f"New position for {items[item_id].itemName} is {data.get('order')}")
        

rflink_data = queue.Queue()
   
class RFLinkActivate:
    def POST(self):
        data = web.input()
        rflink_settings["activated"] = True
        rflink_settings["serial_port"] = data.get("serial_port")
        print(f"serial port: {rflink_settings['serial_port']}")
        get_rflink().connect(rflink_settings["serial_port"])
        with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?showSection=rflink,pulses')

class RFLinkDeactivate:
    def POST(self):
        data = web.input()
        get_rflink().disconnect()
        rflink_settings["activated"] = False
        with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?showSection=rflink,pulses')

class RFLinkDebug:
    def POST(self, debug):
        debug = int(debug)
        rflink_settings["debug"] = False if debug == 0 else True
        with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        if get_rflink().connected:
            get_rflink().disconnect()
            get_rflink().rflink_settings = rflink_settings
            get_rflink().connect(rflink_settings["serial_port"])
        raise web.seeother('/settings?showSection=rflink,pulses')

class SSE:
    def GET(self):
        web.header('Content-Type', 'text/event-stream')
        web.header('Cache-Control', 'no-cache')

        # i = 0
        rflink = get_rflink()
        while True:
            # Read data from the serial port, only when rflink.connected or
            # this will block the serial port and rflink class will not be able to read it
            if rflink.connected and rflink.serial and rflink.serial.isOpen():
                try:
                    data = rflink.serial.readline().decode('utf-8').strip()
                    if data:
                        yield f"data: {data}\n\n\n" #3 \n here to display correctly in textarea
                except Exception as e:
                    print(f"Error reading from serial port: {e}")
            
            time.sleep(0.1) #sleep is necessary in order to not block the app

class RFLinkItemIndex:
    def GET(self):
        return render.index(items)

class RFLinkItemCreate:
    def POST(self):
        data = web.input()
        print(f"rflink_item: {json.dumps(data, indent=4)}")
        # guid = str(uuid.uuid4())
        rflink_item_name = data.get("name")
        rflink_item_mqtt_server = data.get("mqtt_server")
        rflink_item_mqtt_state_publish_topic = data.get("mqtt_state_publish_topic")
        rflink_item_mqtt_command_subscribe_topic = data.get("mqtt_command_subscribe_topic")
        rflink_item_commands = []
        rflink_item_states = []
        rflink_settings["items"].append({
            "name": rflink_item_name,
            "mqtt_server": rflink_item_mqtt_server,
            "mqtt_state_publish_topic": rflink_item_mqtt_state_publish_topic,
            "mqtt_command_subscribe_topic": rflink_item_mqtt_command_subscribe_topic,
            "commands": rflink_item_commands,
            "states": rflink_item_states
        })

        with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?showSection=rflink,item')

class RFLinkItemUpdate:
    def POST(self, item_id):
        item_id = int(item_id)
        data = web.input()
        if item_id < len(rflink_settings["items"]):
            rflink_item_name = data.get("name")
            rflink_item_mqtt_server = data.get("mqtt_server")
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
            guid = str(uuid.uuid4())
            rflink_settings["items"][item_id]["commands"].append({
                "name": data.get("rflink_item_command"),
                "id": guid,
                "pulses":[]
            })
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)
        raise web.seeother('/settings?rflink_item_index=' + str(item_id) + '&showSection=rflink,item')
    
class RFLinkItemStateCreate:
    def POST(self, item_id):
        item_id = int(item_id)
        data = web.input()
        if item_id < len(rflink_settings["items"]):
            guid = str(uuid.uuid4())
            rflink_settings["items"][item_id]["states"].append({
                "name": data.get("rflink_item_state"),
                "id": guid,
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
                state['pulses_exact'].append(get_rflink().processRawPulseLine(state['pulse_middle'], l))
                
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
                state['pulses_shift'].append(get_rflink().processRawPulseLine(state['pulse_middle'], l))
            state["max_common_substring"] = get_rflink().getMaxCommonSubstring(state['pulses_shift'])   
            with open(rflink_file_path, 'w') as f:
                json.dump(rflink_settings, f, indent=4)

            return json.dumps({ "pulses_shift": state['pulses_shift'], "max_common_substring": state["max_common_substring"]})

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
            state["max_common_substring"] = get_rflink().getMaxCommonSubstring(state['pulses_shift'])
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
            print(f"Testing line {i}: {l}")
            if len(l.strip()) == 0:
                print(f"Empty line")
                continue
            results.append({ "line": l, "detection": get_rflink().detect(l, rflink_settings["items"]) })

        return json.dumps(results, indent=4)

app = web.application(urls, locals())

if __name__ == "__main__":
    
    app.run()
