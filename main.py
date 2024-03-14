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
    '/rflink/connect', 'RFLinkConnect',
    '/rflink/disconnect', 'RFLinkDisonnect',
    '/rflink/sse', 'SSE'
)

app = web.application(urls, globals())

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
        data = web.input(showSection="mqtt")
        # print("Sending mqtt_servers: {}".format(json.dumps(mqtt_servers, indent=4)))
        return render.settings(mqtt_servers=mqtt_servers, containers=containers, domains=domains, item_types=item_types, items=items, serial_ports = serial.tools.list_ports.comports(), rflink = { "connected" : rflink.connected, "error" : rflink.connection_error }, showSection=data.showSection)

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

rflink = RFLink()
    
class RFLinkConnect:
    def POST(self):
        data = web.input()
        serial_port = data.get("serial_port")
        print(f"serial port: {serial_port}")
        rflink.connect(serial_port)
        raise web.seeother('/settings?showSection=rflink')

class RFLinkDisonnect:
    def POST(self):
        data = web.input()
        rflink.disconnect()
        raise web.seeother('/settings?showSection=rflink')

class SSE:
    def GET(self):
        web.header('Content-Type', 'text/event-stream')
        web.header('Cache-Control', 'no-cache')

        # i = 0
        while True:
            # Read data from the serial port, only when rflink.connected or
            # this will block the serial port and rflink class will not be able to read it
            if rflink.connected and rflink.serial and rflink.serial.isOpen():
                try:
                    data = rflink.serial.readline().decode('utf-8').strip()
                    if data:
                        yield f"data: ---{data}\n\n\n" #3 \n here to display correctly in textarea
                except Exception as e:
                    print(f"Error reading from serial port: {e}")
            
            time.sleep(0.1) #sleep is necessary in order to not block the app

if __name__ == "__main__":
    app.run()
