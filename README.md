# ehome_v3.0

Install with pip web.py, websocket-client, and paho_mqtt
`pip install web.py paho-mqtt websocket-client packaging`


cd into the project's folder and run with `python main.py` and navigate to `http://0.0.0.0:8080/`

eHome will read the port from `config.json`

run with `python main.py 1234` for a specific port and navigate to `http://0.0.0.0:1234/`



in order to sync the project files with a raspberry pi (or other host) run the `sync_project.sh` script from inside the project folder. The remote host must have ssh installed.

Edit the script to set the rpi address, the destination folder on the remote host, and the username for the ssh connection.

On a windows pc open a wsl terminal where rsync is installed
go to `/mnt/c/Users/YOUR_USER/PATH/TO/PROJECT/ehome_v3.0` and run `./sync_project.sh ./`


For documentation on web.py go to https://webpy.org/docs/0.3/

**Note** In cases like watertank mqtt messages transmitted by the SIP irrigation program, the mqtt payload contains a list of watertank objects. In order for each watertank to be displayed as an individual device in index.html, the item specification in settings uses field `Filter by Id`. In file `static/scripts/watertank.js` the code after parsing the message into a list, it filters the list expecting that each object in the list has a property called "id".

**Note** Items in settings are the items that will be displayed in the index page. RFLink items are the items correspnding to devices sending RFLink messages. In order to display such an item in the index page, create an item in settings and give it a "MQTT Publish Topic", then create an rflink item and give it the same "Mqtt State Publish Topic", and create states for the rflink item that correspond to the states expected by the associated element that will be displayed in the index page.

**Note** Translate works like this `data-translate="home.state.{i.device.state.main}"` i.e. put between single curly brackets the part that you want recalculated at redraw.