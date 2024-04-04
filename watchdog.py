import subprocess
import time
import requests
import argparse
import os

def get_process_info(process_name):
    try:
        output = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq {}".format(process_name)])
        lines = output.decode("utf-8").split("\n")[3:]  # Skip header lines
        return lines
    except subprocess.CalledProcessError:
        return []

def restart_web_app(process_name):
    os.system("taskkill /f /im {}".format(process_name))
    subprocess.Popen(process_name, shell=True)

def health_check(uri):
    try:
        response = requests.get(uri)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def monitor_health(uri):
    while True:
        if not health_check(uri):
            print("Web app is not responding. Gathering process information...")
            process_info = get_process_info(os.path.basename(uri))
            for info in process_info:
                print(info)
            restart_web_app(uri)
        time.sleep(0.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Watchdog for monitoring web app health.')
    parser.add_argument('uri', type=str, help='URI of the web.py app to monitor')
    args = parser.parse_args()
    monitor_health(args.uri)
