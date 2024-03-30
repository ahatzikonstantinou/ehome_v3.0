import serial
import time
import re
import asyncio
import threading
# from contextlib import contextmanager
import queue

import json #for deubugging

class DetectedState:
    def __init__(self, rflink_item, state_name):
        self.rflink_item = rflink_item 
        self.state_name = state_name

# @contextmanager
# def acquire_timeout(lock, timeout):
#     result = lock.acquire(timeout=timeout)
#     try:
#         yield result
#     finally:
#         if result:
#             print(f"Releasing lock")
#             lock.release()

class RFLink:
    CONNECTED_PATTERN = "Nodo RadioFrequencyLink - RFLink Gateway"
    DEBUG_CMD = "10;rfdebug=on;\r\n"
    DEBUG_OK_REPLY = "RFDEBUG=ON;"
    VERSION_CMD = "10;version;\r\n"
    VERSION_REPLY = "VER="
    STATUS_CMD = "10;status;\r\n"
    STATUS_REPLY = "STATUS;"
    RAW_PULSE_PATTERN = ";Pulses(uSec)="
    def __init__(self, rflink_settings):
        self.connected = False
        self.connection_error = ""
        self.serial_port = None
        self.serial = None
        self.command_queue = queue.Queue()
        self.line_queue = queue.Queue()
        self.read_write_thread = threading.Thread(target=self.read_write)
        self.read_write_thread.daemon = True
        self.read_write_thread.start()

        self.rflink_settings = rflink_settings
        if rflink_settings["activated"]:
            print(f"RFLink connecting to {rflink_settings['serial_port']}")
            self.connect(rflink_settings["serial_port"])
    
    def readline(self):
        if not self.line_queue.empty():
            return self.line_queue.get()
        return None
    
    # def readLineIntoQueue(self):
    #     while self.read_write_thread_run:
    #         # print(f"readLineIntoQueue trying to get lock")
    #         # with acquire_timeout(self.lock, 0.001) as acquired:
    #         #     if acquired:
    #         #         print(f"readLineIntoQueue got lock")
    #         if self.serial and self.serial.isOpen():
    #             try:
    #                 if self.serial.in_waiting > 0:
    #                     line = self.serial.readline().decode('utf-8').strip()
    #                     self.line_queue.put(line)
    #             except Exception as e:
    #                 print(f"Error reading from serial: {e}")
    #         time.sleep(0.001)
    
    def sendCommand(self, cmd):
        self.command_queue.put(cmd)

    # def sendCommandFromQueue(self):
    #     while True:
    #         if not self.command_queue.empty():
    #             cmd = self.command_queue.get()
    #             sent = False
    #             print(f"sendCommandFromQueue trying to get lock to send {cmd}")
    #             while not sent:
    #                 with acquire_timeout(self.lock, 0.001) as acquired:
    #                     if acquired:
    #                         print(f"sendCommandFromQueue got lock")
    #                         print(f"self.serial: {self.serial is not None}, isOpen: {self.serial.isOpen()}")
    #                         if self.serial and self.serial.isOpen():
    #                             msg = cmd + "\r\n"
    #                             self.serial.write(msg.encode())
    #                             sent = True
    #                         else:
    #                             raise Exception("Serial is None or not open")

    def read_write(self):
        while True:
            # read any lines waiting in serial
            if self.serial and self.serial.isOpen():
                try:
                    if self.serial.in_waiting > 0:
                        line = self.serial.readline().decode('utf-8').strip()
                        self.line_queue.put(line)
                except Exception as e:
                    print(f"Error reading from serial: {e}")

            # send any command that is in the queue
            if not self.command_queue.empty():
                cmd = self.command_queue.get()
                print(f"Will send command {cmd}")
                if self.serial and self.serial.isOpen():
                    msg = cmd + "\r\n"
                    self.serial.write(msg.encode())
                    print(f"Command {cmd} was sent")
                else:
                    raise Exception("Serial is None or not open")
                
            time.sleep(0.001)       

    def send_initial_command(self):
        # Execute the sequence of expected patterns and commands as observed when RFLink Loader starts logging
        timeout = 10  # Timeout in seconds
        #
        # wait for Node RadioFrequencyLink initial pattern
        #time.sleep(5)
        received_data = self.read_until_pattern_or_timeout(self.CONNECTED_PATTERN, timeout)        
        if received_data is None:
            print(f"Timeout occurred. Could not find pattern {self.CONNECTED_PATTERN}.")
            # return
        print(received_data)
        # #
        # #send version command
        # self.serial.write(self.VERSION_CMD.encode())
        # print(f"Sent: {self.VERSION_CMD.strip()}")
        # time.sleep(1)  # Delay for 1 second after sending the command
        # received_data = self.read_until_pattern_or_timeout(self.VERSION_REPLY, timeout)
        # if received_data is None:
        #     print(f"Timeout occurred. Could not find expected pattern {self.VERSION_REPLY}.")
        #     return
        # print(received_data)
        # #
        # #send status command
        # self.serial.write(self.STATUS_CMD.encode())
        # print(f"Sent: {self.STATUS_CMD.strip()}")
        # time.sleep(1)  # Delay for 1 second after sending the command
        # received_data = self.read_until_pattern_or_timeout(self.STATUS_REPLY, timeout)
        # if received_data is None:
        #     print(f"Timeout occurred. Could not find expected pattern {self.STATUS_REPLY}.")
        #     return
        # print(received_data)

        if self.rflink_settings["debug"]:
            command = self.DEBUG_CMD
            self.serial.write(command.encode())
            print("Initial command sent:", command.strip())
            time.sleep(1)  # Delay for 1 second after sending the command
            received_data = self.read_until_pattern_or_timeout(self.DEBUG_OK_REPLY, timeout)
            if received_data is None:
                print("Timeout occurred. Could not find desired pattern.")
                self.connected = False
                return
            print(received_data)
        self.connected = True

    def read_until_pattern_or_timeout(self, pattern, timeout):
        start_time = time.time()
        received_data = ""
        while time.time() - start_time < timeout:
            if self.serial.in_waiting > 0:
                data = self.serial.readline()
                received_data += data.decode(encoding="ascii", errors="ignore").strip()
                print(f"Reading pattern {received_data}")
                if pattern in received_data:
                    return received_data
        return None

    def connect(self, serial_port):
        self.serial_port = serial_port
        try:
            # print(f"connect trying to get lock")
            # with acquire_timeout(self.lock, 0.1) as acquired:
            #     if acquired:
            #         print(f"connect got lock")
                    if self.serial is not None and self.serial.isOpen():
                        print(f"serial is already connected, will disconnect before reconnecting")
                        self.disconnect(get_lock = False)
                    # Open serial port
                    self.serial = serial.Serial(serial_port, timeout=0)
                    self.serial.close()
                    print(f"Port {serial_port} is now reset")
                    self.serial = serial.Serial(serial_port, baudrate=57600, bytesize=8, stopbits=1, parity=serial.PARITY_NONE, timeout=1)
                    print(f"Port {serial_port} is now created")
                    if self.serial.isOpen():
                        print(f"Port {serial_port} is now open")
                        self.send_initial_command()
                        self.connected = True             
                        return True
                    else:
                        self.connected = False
                        self.connection_error = "No particular error reported"
                        return False
        except serial.SerialException as e:
            print(f"Failed to connect to serial port {serial_port}: {e}")
            self.connected = False
            self.connection_error = e
            return False

    def disconnect(self, get_lock = True):
        # Close serial port
        # if get_lock:
        #     print(f"disconnect trying to get lock")
        #     with acquire_timeout(self.lock, 0.1) as acquired:
        #         if acquired:
        #             print(f"disconnect got lock")
                    if self.serial and self.serial.isOpen():
                        self.serial.close()
                        self.connected = False
                    # else:
                    #     raise Exception("Serial already closed")
        #         else:
        #             raise Exception("Could not get lock on serial. Try again.")
        # else:
        #     if self.serial and self.serial.isOpen():
        #         self.serial.close()
        #         self.connected = False

    def processRawPulseLine(self, pulseMiddle, line):
        if RFLink.RAW_PULSE_PATTERN not in line:
            # remove the sequence id that rflink prefixes each line with
            return ';'.join(line.split(';')[2:])
        
        pulses = RFLink.convert_text_to_binary(line, pulseMiddle, None, None)
        return ''.join([str(p) for p in pulses])

    @staticmethod
    def convert_pulses_to_binary(pulse_data, pulse_mid, pulse_max, pulse_min):
        '''Takes array of strings representing integers, and returns array of 1s and 0s (integers)'''
        binary_values = []
        mx = None
        mn = None
        
        # # if len(pulse_data) < 49:
        # #     # print(f"{len(pulse_data)} < 49. Data rejected.")
        # #     return
        
        # bitstream = 0
        # x = 2
        # while x < len(pulse_data):
        # # for x in range(2, 49, 2):
        #     pulse_int = int(pulse_data[x])
        #     if pulse_int > pulse_mid:
        #         bitstream = (bitstream << 1) | 0x1
        #     else:
        #         bitstream = bitstream << 1
        #     x = x + 2
        #     if x%48 == 0:
        #         print(f"{x} of total {len(pulse_data)} Chuango;ID={bitstream & 0xffffff:06x};SWITCH=02;CMD=ON;")
        #         bitstream = 0
        
        # print(f"{x} of total {len(pulse_data)} Chuango;ID={bitstream & 0xffffff:06x};SWITCH=02;CMD=ON;")    
        # return bitstream

        for pulse in pulse_data:
        
            pulse_int = int(pulse)

            if mx is None or mx < pulse_int:
                mx = pulse_int
            
            if mn is None or mn > pulse_int:
                mn = pulse_int
            
            # if pulse_int > pulse_max:
            #     raise ValueError(f"Pulse value {pulse_int} exceeds PULSEMAX")
            # if pulse_int < pulse_min:
            #     raise ValueError(f"Pulse value {pulse_int} is less than PULSEMIN")
            if pulse_int < pulse_mid:
                binary_values.append(0)
            else:
                binary_values.append(1)
        # print(f"Max: {mx}, Min: {mn}, binary_values: {binary_values}")
        return binary_values

    @staticmethod
    def extract_pulse_data(text):
        match = re.search(r'Pulses\(uSec\)=([^;]+);', text)
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def convert_text_to_binary(text, pulse_mid, pulse_max=None, pulse_min=None):
        '''Takes text with comma separated integers (string), and returns array of 1s and 0s (integers)'''
        pulse_data = RFLink.extract_pulse_data(text)
        # print(f"pulse_data: {pulse_data}")
        if pulse_data is not None:        
            pulse_data_array = pulse_data.split(",")
            # print(f"Got {len(pulse_data_array)} pulses")
            try:
                binary_values = RFLink.convert_pulses_to_binary(pulse_data_array, pulse_mid, pulse_max, pulse_min)
                # print("Binary values:", binary_values)
                return binary_values
            except ValueError as e:
                print("Error:", e)
        else:
            print("Pattern not found or invalid data.")

    @staticmethod
    def getMaxCommonSubstring(lines):
        if not lines:
            return ""

        # Find the shortest string in the list
        shortest = min(lines, key=len)

        # Function to find the longest common substring between two strings
        def find_longest_common_substring(s1, s2):
            matrix = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
            max_length = 0
            end_index = 0

            for i in range(1, len(s1) + 1):
                for j in range(1, len(s2) + 1):
                    if s1[i - 1] == s2[j - 1]:
                        matrix[i][j] = matrix[i - 1][j - 1] + 1
                        if matrix[i][j] > max_length:
                            max_length = matrix[i][j]
                            end_index = i
                    else:
                        matrix[i][j] = 0

            return s1[end_index - max_length: end_index]

        # Find the longest common substring among all pairs of lines
        common_substring = shortest
        for string in lines:
            if string == shortest:
                continue
            common_substring = find_longest_common_substring(common_substring, string)

        return common_substring
    
    @staticmethod
    def detect(line, rflink_items):
        # in results each item has "name", "commands": [], "states": []
        # a command is the command's name, pulse sequence
        # a state is the state's name, exact/max common substring/shift window, pulse sequence
        results = {}
        # print(f"Doing rflink_items:{json.dumps(rflink_items, indent=4)}")
        for i, t in enumerate(rflink_items):
            # print(f"Doing item:{i}")
            # start with dommands
            last_used_pulse_middle = None # used to avoid mutliple convert_text_to_binary with the same pulse_middle
            for c in t['commands']:
                data = line                
                if RFLink.RAW_PULSE_PATTERN in line:
                    if not s['pulse_middle']:
                        # if the command has no pulse_middle defined this raw pulse cannot be
                        # converted to binary and therefore cannot be processed
                        continue
                    if last_used_pulse_middle != c['pulse_middle']:
                        last_used_pulse_middle = c['pulse_middle']
                        data = RFLink.convert_text_to_binary(line, c['pulse_middle'])
                for e in c['pulses_exact']:
                    # print(f"Doing command {e}")
                    if e == data:
                        if i not in results:
                            results[i] = {"name": t['name'], "commands": [], "states": []}
                        results[i]['commands'].append({"name": c['name'], "pulses": e})
            # try states
            last_used_pulse_middle = None   # if data is raw pulses it is converted to string from this point onwards
            data = line
            for s in t['states']:
                # print(f"Doing state {s['name']}")                
                if RFLink.RAW_PULSE_PATTERN in line:
                    if not s['pulse_middle']:
                        # if the state has no pulse_middle defined this raw pulse cannot be
                        # converted to binary and therefore cannot be processed
                        # print(f"It has no pulse_middle, skipping...")
                        continue
                    if last_used_pulse_middle != s['pulse_middle']:
                        last_used_pulse_middle = s['pulse_middle']
                        data = ''.join(str(bit) for bit in RFLink.convert_text_to_binary(line, s['pulse_middle']))
                        # print(f"last_used_pulse_middle != s['pulse_middle'] so I re-converted line to: {data}")
                if s['use_exact_pulse']:
                    for e in s['pulses_exact']:
                        # print(f"Doing state exact ({len(e)}) {e} against ({len(data)}) {data}")
                        if e == data:
                            # print(f"Found it!")
                            if i not in results:
                                results[i] = {"name": t['name'], "commands": [], "states": []}
                            results[i]['states'].append({"name": s["name"], "type": "exact", "pulses": e})
                        # else:
                        #     print(f"They are different")

                if RFLink.RAW_PULSE_PATTERN in line: # only raw pulses are compared using shift window and max_common_substring
                    # print(f"Doing state max_common_substring {s['max_common_substring']}")
                    if s['use_max_common_substring'] and s['max_common_substring'] and s['max_common_substring'] in data:
                        if i not in results:
                            results[i] = {"name": t['name'], "commands": [], "states": []}
                        results[i]['states'].append({"name": s["name"], "type": "max_common_substring", "pulses": s['max_common_substring']})
                    if s['use_shift_window'] and s['shift_window_size'] > 0:
                        for e in s['pulses_shift']:
                            # print(f"Doing state compareAndShift ({len(e)}) {e}")
                            if RFLink.compareAndShift(data, e, s['shift_window_size']):
                                if i not in results:
                                    results[i] = {"name": t['name'], "commands": [], "states": []}
                                # print(f"Appending to states of item {i}")
                                results[i]['states'].append({"name": s["name"], "type": "shift", "pulses": e})    
            
        print(f"Results:{json.dumps(results, indent=4)}")        
        return results

    def detectStates(self, line):
        print(f"Will detect states from line {line}")        
        detectedStates = []
        results = RFLink.detect(line, self.rflink_settings["items"])
        for rflink_item_index, value in results.items():
            rflink_item = self.rflink_settings["items"][rflink_item_index]
            for s in results[rflink_item_index]["states"]:
                if not any(ds.rflink_item["guid"] == rflink_item["guid"] and ds.state_name == s["name"] for ds in detectedStates):
                    detectedStates.append(DetectedState(rflink_item, s["name"]))
                else:
                    print(f"rflink_item: {rflink_item['mqtt_state_publish_topic']}, state: {s['name']} already in the list of detected states")
        
        print(f"Returning {len(detectedStates)} detected states")
        return detectedStates

    def compare(data1, data2):
        # print(f"Comparing data1: {data1}")
        # print(f"with data2: {data2}")
        if len(data1) != len(data2):
            return False
        
        for i in range(len(data1)):
            if data1[i] != data2[i]:
                return False
            
        return True

    @staticmethod
    def compareAndShift(data1, data2, size):
        """
        Compare array data1 against array data2. If data2 is shorter than data1 return False.
        If data2 is longer than data1 choose min(size, len(data1)) and start
        """
        # print(f"len(data1): {len(data1)}, len(data2): {len(data2)}")
        # print(f"data2: {''.join(str(bit) for bit in data2)}")
        # print(f"data1: {''.join(str(bit) for bit in data1)}")
        window = min(len(data1), size)
        # print(f"window: {window}")

        if len(data2) < window:
            return False
        
        found = False
        # print(f"will do {len(data1) - window} shifts in data1")
        for d1 in range(len(data1) - window+1):
            # print(f"Doing shift {d1}")
            for d2 in range(len(data2) - window):        
                found = True
                # print(f"Will compare data1[{d1}] against data2[{d2}]")
                # print(f"data2[0-{d2+window}]: {''.join(str(bit) for bit in data2[:d2+window])}")
                # print(" "*(d2-d1) + f"data1[{d1}-{window}]: {''.join(str(bit) for bit in data1)}")
                for w in range(window):            
                    if data1[d1 + w] != data2[d2 + w]:
                        found = False
                        break;
                if found:
                    break;
            if found:
                # print(f"Found pattern of {window} bits data1[{d1}] in data2[{d2}]")
                # print(f"data2[0-{d2+window}]:  {''.join(str(bit) for bit in data2[:d2+window])}")
                # print(f"data1[{d1}-{window}]:  " + (" "*(d2-d1)) + f"{''.join(str(bit) for bit in data1)}")
                print(f"Found pattern {''.join(str(bit) for bit in data1[d1:window])} of {window} bits data1[{d1}] in data2[{d2}]")
                break

        # print(f"returning found: {found}")
        return found

    # def monitor_serial(port, baudrate, pulse_mid, pulse_max, pulse_min):
    #     ser = serial.Serial(port, baudrate, bytesize=8, stopbits=1, parity=serial.PARITY_NONE)
    #     print(f"Monitoring serial port {port} at {baudrate} baudrate...")
        
    #     try:
    #         send_initial_command(ser)
            
    #         while True:
    #             while ser.in_waiting > 0:
    #                 data = ser.readline().decode().strip()
    #                 match = re.search(r';Pulses=(\d+);', data)
    #                 if match:
    #                     pulses = int(match.group(1))
    #                     match = re.search(r'Pulses\(uSec\)=([^;]+);', data)
                        
    #                     print(f"Received {pulses} pulses")
    #                     # print(f"Data: {data}")
    #                     found = False
    #                     binary_data = convert_text_to_binary(data, pulse_mid, pulse_max, pulse_min)
    #                     for i in range(len(str_data)):
    #                         known_binary_values = convert_pulses_to_binary(str_data[i].split(","), pulse_mid, pulse_max, pulse_min)
    #                         # print(f"known_binary_values = {''.join(str(bit) for bit in known_binary_values)}")
    #                         # print(f"binary_data         = {''.join(str(bit) for bit in binary_data)}")
    #                         if compare(binary_data, known_binary_values):
    #                             print(f"binary_data         = {''.join(str(bit) for bit in binary_data)}")
    #                             found = True
    #                             break
    #                         else:
    #                             # print("Trying compare and shift")
    #                             found = compareAndShift(binary_data, known_binary_values, 50)
    #                             if found:
    #                                 print(f"***Found data with compareAndShift")
    #                                 break;

    #                     if found:
    #                         print(f"*Known data from pos{i} {pulses} pulses")
    #                     else:
    #                         print(f"Unknown data {pulses} pulses.")

    #     except KeyboardInterrupt:
    #         ser.close()
    #         print("Serial monitoring stopped.")

    # str_data = [
    #     # "570,1650,510,1650,510,1650,510,1650,510,1650,510,1650,510,1650,510,1650,510,1650,1680,480,510,1650,1680,480,1680,480,510,1650,510,1650,1680,480,510,1650,510,1650,510,1650,510,1650,510,1650,510,1650,510,1680,1680,480,510,6990",
    #     # "540,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,480,1590,480,1590,450,1590,450,1590,1560,480,480,1590,1560,510,1560,510,1560,510,1560,480,480,1590,1560,480,1560,480,1560,480,450,6990",
    #     # "510,1500,450,1500,420,1500,1470,480,450,1590,1560,480,1560,480,1560,510,1560,480,450,1590,1560,480,1560,480,1560,480,450,6990",
    #     # "570,450,1470,450,1470,450,420,1500,1500,480,1560,510,450,1590,450,1590,450,1590,480,1590,480,1590,1560,480,450,1590,1560,510,1560,480,1560,480,1560,480,450,1590,1560,480,1560,480,1560,480,480,6990",
    #     # "510,1500,420,1500,450,1500,420,1500,420,1590,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,480,1590,1560,480,1560,480,1560,480,450,6990",
    #     # "1560,450,450,1500,1500,450,1470,480,450,1590,480,1590,480,1590,480,1590,450,1590,1560,480,480,1590,1560,480,1560,480,1560,480,1560,480,480,1590,1560,480,1560,480,1560,480,480,6990",
    #     # "330,450,1470,450,450,1500,420,1500,450,1500,480,1590,480,1560,1560,480,480,1590,1560,480,1560,480,1560,480,1560,480,450,1590,1560,480,1560,480,1560,450,480,6990",
    #     # "240,1500,1470,450,1470,480,450,1500,420,1560,450,1590,450,1590,480,1560,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,480,1590,1560,480,1560,480,1560,450,480,6990",
    #     # "1560,450,1470,480,450,1500,450,1500,450,1590,480,1590,450,1590,1560,480,480,1590,1560,480,1560,510,1560,480,1560,480,480,1590,1560,480,1560,480,1560,480,450,6990",
    #     # "90,1500,1500,450,1470,480,450,1500,420,1560,480,1590,480,1590,480,1560,1560,480,450,1590,1560,480,1560,480,1560,480,1560,480,450,1590,1560,480,1560,480,1560,450,450,6990",
    #     # "1560,450,1470,480,450,1500,420,1500,450,1590,480,1590,480,1560,1560,480,450,1590,1560,510,1560,480,1560,480,1560,480,480,1590,1560,480,1560,480,1560,450,480,6990",
    #     # "60,1500,1500,450,1470,480,450,1500,420,1560,480,1590,450,1590,450,1590,1560,480,480,1590,1560,480,1560,510,1560,480,1560,480,480,1590,1560,480,1560,480,1560,480,450,6990",
    #     # "1560,450,1470,480,450,1500,420,1500,450,1590,480,1590,450,1590,1560,480,450,1590,1560,480,1560,480,1560,480,1560,480,450,1590,1560,480,1560,480,1560,6990",
    #     "540,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,450,1590,450,1590,450,1590,480,1590,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,450,1590,450,1560,480,4350,450,1590,480,1590,480,1590,1560,480,1560,480,1560,480,480,1590,1560,510,1560,510,450,1590,450,1590,480,1590,480,1590,480,1590,1560,480,450,1590,1560,480,1560,480,1560,510,1560,480,1560,480,1560,480,480,1590,480,1560,450,4350,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,480,1590,450,1590,450,1590,450,1590,1560,480,450,1590,1560,510,1560,510,1560,510,1560,480,1560,480,1560,480,450,1590,450,1560,450,4350,450,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,450,1590,450,1590,450,1590,480,1590,450,1590,1560,480,450,1590,1560,510,1560,480,1560,480,1560,510,1560,510,1560,510,450,990",
    #     "510,1590,480,1560,480,1560,1560,480,1560,480,1560,480,450,1560,1560,480,480,1590,450,1590,1560,480,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,450,1560,450,4320,450,1590,480,1590,450,1560,1560,480,1560,480,1560,480,450,1560,1560,480,480,1590,450,1590,1560,480,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,450,1560,480,4320,450,1590,480,1560,480,1560,1560,480,1560,480,1560,480,450,1560,1560,480,480,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,450,1560,480,4320,450,1590,450,1590,450,1560,1560,480,1560,480,1560,480,450,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,480,1590,450,1560,1560,480,1560,480,1560,480,480,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,480,1560,480,1560,1560,480,1560,480,1560,480,480,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,480,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,480,1590,450,1590,1560,480,1560,480,1560,480,480,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,450,4320,480,1590,450,1560,450,1590,1560,480,1560,480,1560,480,480,1560,1560,510,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,480,1560,480,1560,480,4320,480,1590,480,1560,450,1590,1560,480,1560,480,1560,480,480,1560,1560,510,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,480,1560,450,1590,1560,480,1560,480,1560"
    # ]
    # test_data = [
    #     "540,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,480,480,1590,480,1590,450,1590,450,1590,450,1590,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,450,1590,450,1560,450,4350,450,1590,480,1590,480,1590,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,450,1590,450,1590,450,1590,480,1590,480,1590,1560,480,450,1590,1560,510,1560,480,1560,480,1560,510,1560,480,1560,480,480,1590,480,1560,480,4350,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,480,1590,1560,510,1560,510,450,1590,480,1590,480,1590,450,1590,450,1590,1560,480,480,1590,1560,510,1560,510,1560,510,1560,480,1560,480,1560,480,450,1590,450,1560,450,4350,450,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,450,1590,450,1590,450,1590,450,1590,1560,480,450,1590,1560,510,1560,510,1560,480,1560,480,1560,510,1560,480,450,1590,450,1560,450,4350,450,1590,480,1590,450,1590,1560,480,1560,480,1560,480,480,1590,1560,510,1560,510,450,1590,450,1590,480,1590,480,1590,450,1590,1560,480,450,1590,1560,480,1560,480,1560,510,1560,480,1560,480,1560,480,480,1560,480,1560,450,4350,450,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,480,1590,450,1590,450,1590,450,1590,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,450,1590,450,1560,450,4350,450,1590,480,1590,480,1590,1560,480,1560,480,1560,480,480,1590,1560,510,1560,510,450,1590,450,1590,450,1590,480,1590,480,1590,1560,480,450,1590,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,480,1560,480,1560,480,4350,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,450,1590,480,1590,480,1590,450,1590,450,1590,1560,480,480,1590,1560,480,1560,510,1560,510,1560,480,1560,480,1560,480,480,1590,450,1560,450,4350,450,1590,450,1590,480,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,480,480,1590,450,1590,450,1590,450,1590,480,1560,1560,480,450,1590,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4350,480,1590,480,1590,480,1590,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,450,1590,450,1590,480,1590,480,1590,450,1590,1560,480,450,1590,1560,480,1560,480,1560,510,1560,480,1560,480,1560,480,480,1590,480,1560,450,4350,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450"
    # ]

# if __name__ == "__main__":
#     port = "COM6"  # Change this to your serial port
#     baudrate = 57600  # Change this to match your device's baud rate
#     RAWSIGNAL_SAMPLE_RATE = 30
#     PULSECOUNT = 50
#     PULSEMID = 1000 #700 / RAWSIGNAL_SAMPLE_RATE
#     PULSEMAX = 2000 / RAWSIGNAL_SAMPLE_RATE
#     PULSEMIN = 150 / RAWSIGNAL_SAMPLE_RATE
#     monitor_serial(port, baudrate, PULSEMID, PULSEMAX, PULSEMIN)
#     i = 0
#     binary_data = convert_pulses_to_binary(test_data[0].split(","), PULSEMID, PULSEMAX, PULSEMIN)

#     known_binary_values = convert_pulses_to_binary(str_data[13].split(","), PULSEMID, PULSEMAX, PULSEMIN)
#     compareAndShift(binary_data, known_binary_values, 48)
#     exit
#     # for s in str_data:
#     #     print(f"Doing {i} with len:{len(s)}")
#     #     i+=1
#     #     # convert_text_to_binary(s, PULSEMID, PULSEMAX, PULSEMIN)
#     #     known_binary_values = convert_pulses_to_binary(s.split(","), PULSEMID, PULSEMAX, PULSEMIN)
#     #     compareAndShift(binary_data, known_binary_values, 48)
#     #     # break
        

