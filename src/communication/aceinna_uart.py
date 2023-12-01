import os
import sys
import time
import curses
import serial
import threading
import collections

from ..common.print_center import pass_print, error_print
from ..common.Jsonf_Creater import JsonCreat

class Uart:
    def __init__(self, port, baud, odr=100):
        self.port_name = port
        self.baud_rate = baud
        self.odr = odr
        self.ser = None
        self.isLog = False
        self.tlock = threading.Lock()
        self.myqueue = collections.deque(maxlen=1000 * self.odr)
        self.pkt_info_dict = {
            'S1': ([0x53, 0x31], 31),
            'S2': ([0x53, 0x32], 45),
            'F1': ([0x46, 0x31], 61),
            'A1': ([0x43, 0x31], 39),
            'FM': ([0x46, 0x4D], 123),
            'S3': ([0x55, 0xAA, 0x24], 40),
            'AT': ([0xBD, 0XDB, 0x54], 39)
        }

    def ser_init(self):
        try:
            self.ser = serial.Serial(self.port_name, 
                                    self.baud_rate,
                                    parity=serial.PARITY_NONE,
                                    stopbits=serial.STOPBITS_ONE, 
                                    bytesize=serial.EIGHTBITS,
                                    timeout=1)
            self.ser.set_buffer_size(rx_size=2048, tx_size=2048)
        except serial.SerialException as e:
            error_print("Error occurred while trying to create serial port")
            self.ser = None

        if self.ser is not None:
            if self.ser.isOpen():
                pass_print("Serial port is successfully created and open.")
            else:
                error_print("Serial port is created but not open.")
        else:
            sys.exit(0)
            error_print("Serial port is not created.")

    def ser_close(self):
        if self.ser is not None:
            if self.ser.isOpen():
                self.ser.flushInput()
                self.ser.flushOutput()
                self.ser.close()
                pass_print("Serial port is closed.")

    def rev_data_to_buffer(self, data_length):
        '''
        This function is used to receive and play serial port data
        '''
        buffer = bytearray()
        self.isLog = True
        while self.isLog:
            if self.ser.in_waiting >= data_length:
                data = self.ser.read(data_length)
                buffer.extend(data)
                while len(buffer) >= data_length:
                    packet = buffer[:data_length]
                    self.tlock.acquire()
                    self.myqueue.append(bytes(packet))
                    self.tlock.release()
                    buffer = buffer[data_length:]

    def log_data_to_file(self, logf_name):
        while self.isLog == False:
            time.sleep(0.1)
        data_dir = ".\data"
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        logf = open(logf_name, 'wb')
        timeout = 1 / self.odr
        while self.isLog:
            if len(self.myqueue) > 0:
                data = self.myqueue.popleft()
                logf.write(data)
            time.sleep(timeout)

    def data_log(self, data_type, logf_name, stdscr):
        data_length = self.pkt_info_dict.get(data_type)[1]

        rev_thread = threading.Thread(target=self.rev_data_to_buffer, args=(data_length,))
        log_thread = threading.Thread(target=self.log_data_to_file, args=(logf_name,))
        for t in [rev_thread, log_thread]:
            t.start()
        stdscr.addstr(2, 0, "Press 'S' to stop logging.")
        stdscr.refresh()
        key = stdscr.getch()
        while key != ord('s'):
            key = stdscr.getch()
        self.isLog = False
        stdscr.move(2, 0)
        stdscr.clrtoeol()
        stdscr.addstr(2, 0, "Data logging finished.")
        stdscr.refresh()
        for t in [rev_thread, log_thread]:
            t.join()

    '''TODO: def write_read_response(self, msg):
    '''
   
    def realtime_data(self, data_type, parser):
        '''
        data_type: The type of the data to be visualized
        parser: parse function of data
        '''
        idx = 20 if self.odr > 50 else 25 if self.odr == 50 else self.odr
        cnt = 0
        x, y, z = 4, 5, -2 # Aceinna packet protocol: x(num of packet type bytes) y(num of packet type bytes + num of payload length bytes) z(negative num of crc bytes) 
        packet_type_payload = [0x55, 0x55] + self.pkt_info_dict[data_type][0]
        data_length = self.pkt_info_dict.get(data_type)[1]
        if data_type == 'S1':
            target_data_pos = [0, 1, 2, 3, 4, 5]
        elif data_type == 'S2':
            target_data_pos = [2, 3, 4, 5, 6, 7]
        elif data_type == 'S3':
            x, y, z = 3, 3, -1
            target_data_pos = [4, 5, 6, 1, 2, 3]
            packet_type_payload = self.pkt_info_dict[data_type][0]
        elif data_type == 'A1':
            target_data_pos = [6, 7, 8, 3, 4, 5]
        elif data_type == 'A2':
            target_data_pos = [6, 7, 8, 3, 4, 5]
        elif data_type == 'FM':
            '''This packet is not supported to visualize
            '''
            return
        elif data_type == 'AT':
            x, y, z = 3, 3, -2
            target_data_pos = [3, 4, 5, 0, 1, 2]
            packet_type_payload = self.pkt_info_dict[data_type][0]

        rev_thread = threading.Thread(target=self.rev_data_to_buffer, args=(data_length,))
        rev_thread.start() 
        time.sleep(0.1)
        while self.isLog:
            if len(self.myqueue) != 0:
                data = self.myqueue.popleft()
                if data[:x] == bytes(packet_type_payload):
                    cnt += 1
                    if cnt == self.odr / idx:
                        payload = data[y:z]
                        latest = parser(payload)
                        mylatest = [latest[i] for i in target_data_pos]
                        cnt = 0
                        yield mylatest