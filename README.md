# ehome_v3.0

Install with pip web.py, websocket-client, and paho_mqtt
`pip install web.py paho-mqtt websocket-client`

cd into the project's folder and run with `python main.py` and navigate to `http://0.0.0.0:8080/`

run with `python main.py 1234` for a specific port and navigate to `http://0.0.0.0:1234/`

in order to sync the project files with a raspberry pi (or other host) run the `sync_project.sh` script from inside the project folder. The remote host must have ssh installed.

Edit the script to set the rpi address, the destination folder on the remote host, and the username for the ssh connection.

On a windows pc open a wsl terminal where rsync is installed
go to `/mnt/c/Users/YOUR_USER/PATH/TO/PROJECT/ehome_v3.0` and run `./sync_project.sh ./`

For documentation on web.py go to https://webpy.org/docs/0.3/