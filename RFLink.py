import serial
import time
import re
import asyncio
import websockets
import threading

class RFLink:
    CONNECTED_PATTERN = "Nodo RadioFrequencyLink - RFLink Gateway"
    DEBUG_CMD = "10;rfdebug=on;\r\n"
    DEBUG_OK_REPLY = "RFDEBUG=ON;"
    def __init__(self):
        self.connected = False
        self.connection_error = ""
        self.serial_port = None
        self.serial = None
    
    def read_and_send(self):
        # Create an event loop
        while self.serial and self.serial.isOpen():
            try:
                # Read from serial port                    
                data = self.serial.readline().decode('utf-8').strip()
                if data:
                    # data += "\n"
                    print(f"Read serial data: {data}")
            except Exception as e:
                print(f"Error reading from serial port: {e}")

    def send_initial_command(self):
        timeout = 5  # Timeout in seconds
        time.sleep(1)  # Delay for 1 second before sending the command
        received_data = self.read_until_pattern_or_timeout(self.CONNECTED_PATTERN, timeout)
        
        if received_data is None:
            print("Timeout occurred. Could not find desired pattern.")
            return
        print(received_data)
        
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
                received_data += self.serial.readline().decode().strip()
                if pattern in received_data:
                    return received_data
        return None

    def connect(self, serial_port):
        self.serial_port = serial_port
        try:
            # Open serial port
            self.serial = serial.Serial(serial_port, baudrate=57600, bytesize=8, stopbits=1, parity=serial.PARITY_NONE, timeout=1)
            if self.serial.isOpen():
                self.send_initial_command()
                self.connected = True             
                return True
            else:
                self.connected = False
                self.connection_error = "No particular error reported"
                return False
        except serial.SerialException as e:
            print(f"Failed to connect to serial port {port}: {e}")
            self.connected = False
            self.connection_error = e
            return False

    def disconnect(self):
        # Close serial port
        if self.serial and self.serial.isOpen():
            self.serial.close()
            self.connected = False

    def convert_pulses_to_binary(pulse_data, pulse_mid, pulse_max, pulse_min):
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

    def extract_pulse_data(text):
        match = re.search(r'Pulses\(uSec\)=([^;]+);', text)
        if match:
            return match.group(1)
        else:
            return None

    def convert_text_to_binary(text, pulse_mid, pulse_max, pulse_min):
        pulse_data = extract_pulse_data(text)
        # print(f"pulse_data: {pulse_data}")
        if pulse_data is not None:        
            pulse_data_array = pulse_data.split(",")
            # print(f"Got {len(pulse_data_array)} pulses")
            try:
                binary_values = convert_pulses_to_binary(pulse_data_array, pulse_mid, pulse_max, pulse_min)
                # print("Binary values:", binary_values)
                return binary_values
            except ValueError as e:
                print("Error:", e)
        else:
            print("Pattern not found or invalid data.")

    def compare(data1, data2):
        # print(f"Comparing data1: {data1}")
        # print(f"with data2: {data2}")
        if len(data1) != len(data2):
            return False
        
        for i in range(len(data1)):
            if data1[i] != data2[i]:
                return False
            
        return True

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

    def monitor_serial(port, baudrate, pulse_mid, pulse_max, pulse_min):
        ser = serial.Serial(port, baudrate, bytesize=8, stopbits=1, parity=serial.PARITY_NONE)
        print(f"Monitoring serial port {port} at {baudrate} baudrate...")
        
        try:
            send_initial_command(ser)
            
            while True:
                while ser.in_waiting > 0:
                    data = ser.readline().decode().strip()
                    match = re.search(r';Pulses=(\d+);', data)
                    if match:
                        pulses = int(match.group(1))
                        match = re.search(r'Pulses\(uSec\)=([^;]+);', data)
                        
                        print(f"Received {pulses} pulses")
                        # print(f"Data: {data}")
                        found = False
                        binary_data = convert_text_to_binary(data, pulse_mid, pulse_max, pulse_min)
                        for i in range(len(str_data)):
                            known_binary_values = convert_pulses_to_binary(str_data[i].split(","), pulse_mid, pulse_max, pulse_min)
                            # print(f"known_binary_values = {''.join(str(bit) for bit in known_binary_values)}")
                            # print(f"binary_data         = {''.join(str(bit) for bit in binary_data)}")
                            if compare(binary_data, known_binary_values):
                                print(f"binary_data         = {''.join(str(bit) for bit in binary_data)}")
                                found = True
                                break
                            else:
                                # print("Trying compare and shift")
                                found = compareAndShift(binary_data, known_binary_values, 50)
                                if found:
                                    print(f"***Found data with compareAndShift")
                                    break;

                        if found:
                            print(f"*Known data from pos{i} {pulses} pulses")
                        else:
                            print(f"Unknown data {pulses} pulses.")

        except KeyboardInterrupt:
            ser.close()
            print("Serial monitoring stopped.")

    str_data = [
        # "570,1650,510,1650,510,1650,510,1650,510,1650,510,1650,510,1650,510,1650,510,1650,1680,480,510,1650,1680,480,1680,480,510,1650,510,1650,1680,480,510,1650,510,1650,510,1650,510,1650,510,1650,510,1650,510,1680,1680,480,510,6990",
        # "540,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,480,1590,480,1590,450,1590,450,1590,1560,480,480,1590,1560,510,1560,510,1560,510,1560,480,480,1590,1560,480,1560,480,1560,480,450,6990",
        # "510,1500,450,1500,420,1500,1470,480,450,1590,1560,480,1560,480,1560,510,1560,480,450,1590,1560,480,1560,480,1560,480,450,6990",
        # "570,450,1470,450,1470,450,420,1500,1500,480,1560,510,450,1590,450,1590,450,1590,480,1590,480,1590,1560,480,450,1590,1560,510,1560,480,1560,480,1560,480,450,1590,1560,480,1560,480,1560,480,480,6990",
        # "510,1500,420,1500,450,1500,420,1500,420,1590,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,480,1590,1560,480,1560,480,1560,480,450,6990",
        # "1560,450,450,1500,1500,450,1470,480,450,1590,480,1590,480,1590,480,1590,450,1590,1560,480,480,1590,1560,480,1560,480,1560,480,1560,480,480,1590,1560,480,1560,480,1560,480,480,6990",
        # "330,450,1470,450,450,1500,420,1500,450,1500,480,1590,480,1560,1560,480,480,1590,1560,480,1560,480,1560,480,1560,480,450,1590,1560,480,1560,480,1560,450,480,6990",
        # "240,1500,1470,450,1470,480,450,1500,420,1560,450,1590,450,1590,480,1560,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,480,1590,1560,480,1560,480,1560,450,480,6990",
        # "1560,450,1470,480,450,1500,450,1500,450,1590,480,1590,450,1590,1560,480,480,1590,1560,480,1560,510,1560,480,1560,480,480,1590,1560,480,1560,480,1560,480,450,6990",
        # "90,1500,1500,450,1470,480,450,1500,420,1560,480,1590,480,1590,480,1560,1560,480,450,1590,1560,480,1560,480,1560,480,1560,480,450,1590,1560,480,1560,480,1560,450,450,6990",
        # "1560,450,1470,480,450,1500,420,1500,450,1590,480,1590,480,1560,1560,480,450,1590,1560,510,1560,480,1560,480,1560,480,480,1590,1560,480,1560,480,1560,450,480,6990",
        # "60,1500,1500,450,1470,480,450,1500,420,1560,480,1590,450,1590,450,1590,1560,480,480,1590,1560,480,1560,510,1560,480,1560,480,480,1590,1560,480,1560,480,1560,480,450,6990",
        # "1560,450,1470,480,450,1500,420,1500,450,1590,480,1590,450,1590,1560,480,450,1590,1560,480,1560,480,1560,480,1560,480,450,1590,1560,480,1560,480,1560,6990",
        "540,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,450,1590,450,1590,450,1590,480,1590,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,450,1590,450,1560,480,4350,450,1590,480,1590,480,1590,1560,480,1560,480,1560,480,480,1590,1560,510,1560,510,450,1590,450,1590,480,1590,480,1590,480,1590,1560,480,450,1590,1560,480,1560,480,1560,510,1560,480,1560,480,1560,480,480,1590,480,1560,450,4350,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,480,1590,450,1590,450,1590,450,1590,1560,480,450,1590,1560,510,1560,510,1560,510,1560,480,1560,480,1560,480,450,1590,450,1560,450,4350,450,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,450,1590,450,1590,450,1590,480,1590,450,1590,1560,480,450,1590,1560,510,1560,480,1560,480,1560,510,1560,510,1560,510,450,990",
        "510,1590,480,1560,480,1560,1560,480,1560,480,1560,480,450,1560,1560,480,480,1590,450,1590,1560,480,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,450,1560,450,4320,450,1590,480,1590,450,1560,1560,480,1560,480,1560,480,450,1560,1560,480,480,1590,450,1590,1560,480,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,450,1560,480,4320,450,1590,480,1560,480,1560,1560,480,1560,480,1560,480,450,1560,1560,480,480,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,450,1560,480,4320,450,1590,450,1590,450,1560,1560,480,1560,480,1560,480,450,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,480,1590,450,1560,1560,480,1560,480,1560,480,480,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,480,1560,480,1560,1560,480,1560,480,1560,480,480,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,480,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,480,1590,450,1590,1560,480,1560,480,1560,480,480,1560,1560,480,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,450,4320,480,1590,450,1560,450,1590,1560,480,1560,480,1560,480,480,1560,1560,510,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,480,1560,480,1560,480,4320,480,1590,480,1560,450,1590,1560,480,1560,480,1560,480,480,1560,1560,510,450,1590,450,1590,1560,480,1560,480,1560,480,1560,480,450,1560,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4320,480,1590,480,1560,450,1590,1560,480,1560,480,1560"
    ]
    test_data = [
        "540,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,480,480,1590,480,1590,450,1590,450,1590,450,1590,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,450,1590,450,1560,450,4350,450,1590,480,1590,480,1590,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,450,1590,450,1590,450,1590,480,1590,480,1590,1560,480,450,1590,1560,510,1560,480,1560,480,1560,510,1560,480,1560,480,480,1590,480,1560,480,4350,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,480,1590,1560,510,1560,510,450,1590,480,1590,480,1590,450,1590,450,1590,1560,480,480,1590,1560,510,1560,510,1560,510,1560,480,1560,480,1560,480,450,1590,450,1560,450,4350,450,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,450,1590,450,1590,450,1590,450,1590,1560,480,450,1590,1560,510,1560,510,1560,480,1560,480,1560,510,1560,480,450,1590,450,1560,450,4350,450,1590,480,1590,450,1590,1560,480,1560,480,1560,480,480,1590,1560,510,1560,510,450,1590,450,1590,480,1590,480,1590,450,1590,1560,480,450,1590,1560,480,1560,480,1560,510,1560,480,1560,480,1560,480,480,1560,480,1560,450,4350,450,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,510,480,1590,480,1590,450,1590,450,1590,450,1590,1560,480,480,1590,1560,510,1560,510,1560,480,1560,480,1560,480,1560,480,450,1590,450,1560,450,4350,450,1590,480,1590,480,1590,1560,480,1560,480,1560,480,480,1590,1560,510,1560,510,450,1590,450,1590,450,1590,480,1590,480,1590,1560,480,450,1590,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,480,1560,480,1560,480,4350,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,450,1590,480,1590,480,1590,450,1590,450,1590,1560,480,480,1590,1560,480,1560,510,1560,510,1560,480,1560,480,1560,480,480,1590,450,1560,450,4350,450,1590,450,1590,480,1590,1560,480,1560,480,1560,480,450,1590,1560,510,1560,480,480,1590,450,1590,450,1590,450,1590,480,1560,1560,480,450,1590,1560,510,1560,480,1560,480,1560,480,1560,480,1560,480,450,1560,480,1560,480,4350,480,1590,480,1590,480,1590,1560,480,1560,480,1560,480,480,1560,1560,510,1560,510,450,1590,450,1590,480,1590,480,1590,450,1590,1560,480,450,1590,1560,480,1560,480,1560,510,1560,480,1560,480,1560,480,480,1590,480,1560,450,4350,480,1590,450,1590,450,1590,1560,480,1560,480,1560,480,450"
    ]

if __name__ == "__main__":
    port = "COM6"  # Change this to your serial port
    baudrate = 57600  # Change this to match your device's baud rate
    RAWSIGNAL_SAMPLE_RATE = 30
    PULSECOUNT = 50
    PULSEMID = 1000 #700 / RAWSIGNAL_SAMPLE_RATE
    PULSEMAX = 2000 / RAWSIGNAL_SAMPLE_RATE
    PULSEMIN = 150 / RAWSIGNAL_SAMPLE_RATE
    monitor_serial(port, baudrate, PULSEMID, PULSEMAX, PULSEMIN)
    i = 0
    binary_data = convert_pulses_to_binary(test_data[0].split(","), PULSEMID, PULSEMAX, PULSEMIN)

    known_binary_values = convert_pulses_to_binary(str_data[13].split(","), PULSEMID, PULSEMAX, PULSEMIN)
    compareAndShift(binary_data, known_binary_values, 48)
    exit
    # for s in str_data:
    #     print(f"Doing {i} with len:{len(s)}")
    #     i+=1
    #     # convert_text_to_binary(s, PULSEMID, PULSEMAX, PULSEMIN)
    #     known_binary_values = convert_pulses_to_binary(s.split(","), PULSEMID, PULSEMAX, PULSEMIN)
    #     compareAndShift(binary_data, known_binary_values, 48)
    #     # break
        
