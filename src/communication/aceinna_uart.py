import os
import sys
import time
import curses
import serial
import struct
import asyncio
import threading
import collections
import numpy as np

from ..common.print_center import pass_print, error_print
from ..common.Jsonf_Creater import JsonCreate

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
            'A1': ([0x41, 0x31], 39),
            'A2': ([0x41, 0x32], 37),
            'FM': ([0x46, 0x4D], 95),
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
                                    timeout=0.1)
            self.ser.set_buffer_size(rx_size=2048, tx_size=2048)
        except serial.SerialException as e:
            error_print("Error occurred while trying to create serial port")
            self.ser = None

        if self.ser is not None:
            if self.ser.isOpen():
                # pass_print("Serial port is successfully created and open.")
                pass
            else:
                error_print("Serial port is created but not open.")
        else:
            sys.exit(0)
            error_print("Serial port is not created.")

    def ser_close(self):
        if self.ser is not None:
            if self.ser.isOpen():
                self.ser.close()
                # pass_print("Serial port is closed.")

    def rev_data_to_buffer(self, data_type, data_length):
        '''
        This function is used to receive and play serial port data
        '''
        buffer = b''
        self.isLog = True
        self.ser.flushInput()
        self.ser.flushOutput()
        while self.isLog:
            data_size = self.ser.in_waiting
            data = self.ser.read(data_size)
            buffer += data
            while len(buffer) >= data_length:
                packet_header_pos = buffer.find(data_type)
                packet_ender_pos = packet_header_pos + data_length
                if packet_header_pos != -1 and packet_ender_pos <= len(buffer):
                    packet = buffer[packet_header_pos: packet_ender_pos]
                    self.tlock.acquire()
                    self.myqueue.append(bytes(packet))
                    self.tlock.release()
                    buffer = buffer[packet_ender_pos:]
                else:
                    break
            time.sleep(0.01)
        self.myqueue.clear()

    async def rev_data_to_buffer_(self, data_type, data_length):
        '''
        This function is used to receive and play serial port data
        '''
        buffer = b''
        self.isLog = True
        self.ser.flushInput()
        self.ser.flushOutput()
        while self.isLog:
            data_size = self.ser.in_waiting
            data = self.ser.read(data_size)
            buffer += data
            while len(buffer) >= data_length:
                packet_header_pos = buffer.find(data_type)
                packet_ender_pos = packet_header_pos + data_length
                if packet_header_pos != -1 and packet_ender_pos <= len(buffer):
                    packet = buffer[packet_header_pos: packet_ender_pos]
                    self.myqueue.append(bytes(packet))
                    buffer = buffer[packet_ender_pos:]
                else:
                    break
            await asyncio.sleep(0.01)
        self.myqueue.clear()

    async def log_data_to_file_(self, logf_name):
        while self.isLog == False:
            await asyncio.sleep(0.1)
        data_dir = ".\data"
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        logf = open(logf_name, 'wb')
        timeout = 1 / self.odr
        while self.isLog:
            while len(self.myqueue) > 0:
                data = self.myqueue.popleft()
                logf.write(data)
            await asyncio.sleep(timeout)

    async def data_log_(self, data_type, logf_name, stdscr):
        data_length = self.pkt_info_dict.get(data_type)[1]
        if data_type == 'S3' or data_type == 'AT':
            data_type = bytes(self.pkt_info_dict.get(data_type)[0])
        else:
            data_type = bytes([0x55,0x55] + self.pkt_info_dict.get(data_type)[0])

        async def supervisory_(stdscr):
            stdscr.nodelay(True)
            stdscr.addstr(2, 0, "Press 'S' to stop logging.")
            stdscr.refresh()
            key = stdscr.getch()
            while key != ord('s'):
                key = stdscr.getch()
                await asyncio.sleep(0.01)
            self.isLog = False
            stdscr.move(2, 0)
            stdscr.clrtoeol()
            stdscr.addstr(2, 0, "Data logging finished.")
            stdscr.refresh()
  
        await asyncio.gather(
            self.rev_data_to_buffer_(data_type, data_length),
            self.log_data_to_file_(logf_name),
            supervisory_(stdscr)
        )

    def data_log(self, data_type, logf_name, stdscr):
        asyncio.run(self.data_log_(data_type, logf_name, stdscr)) 
        
    def write_read_response(self, packet, resp_length=None):
        self.ser.write(packet)
        start_time = time.time()
        resp_pos = -1
        data = b''
        while time.time() - start_time < 3:
            read_size = self.ser.in_waiting
            data += self.ser.read(read_size)
            if packet[:4] == bytes([0x55, 0x55, 0x47, 0x50]): # UUGP
                resp_header = packet[:2] + packet[5:7]
            else:
                resp_header = packet[:4]
            resp_pos = data.find(resp_header)
            if resp_pos != -1:
                try:
                    resp_length = data[resp_pos+4]
                except:
                    continue
                resp = data[resp_pos: resp_pos + resp_length + 7]
                if len(resp) == resp_length + 7:
                    return True, resp
        return False, None

    def pkt_info_update(self, data_type):
        if data_type == 'S3' or data_type == 'AT':
            return
        data_type_payload = bytes([0x55, 0x55] + self.pkt_info_dict[data_type][0])
        data = b''
        start_time = time.time()
        while time.time() - start_time < 3:
            read_size = self.ser.in_waiting
            data += self.ser.read(read_size)
            data_header_pos = data.find(data_type_payload)
            if data_header_pos != -1 and len(data) >= data_header_pos + 5:
                data_length = data[data_header_pos + 4] + 7
                self.pkt_info_dict[data_type] = (self.pkt_info_dict[data_type][0], data_length)
                break
        
    def realtime_data(self, stdscr, data_type, parser):
        '''
        data_type: The type of the data to be visualized
        parser: parse function of data
        '''
        idx = 20 if self.odr > 50 else 10 if self.odr == 50 else self.odr # 20hz
        cnt = 0
        retry_times = 0
        x, y, z = 4, 5, -2 # Aceinna packet protocol: x(num of packet type bytes) y(num of packet type bytes + num of payload length bytes) z(negative num of crc bytes) 
        packet_type_payload = [0x55, 0x55] + self.pkt_info_dict[data_type][0]
        data_length = self.pkt_info_dict.get(data_type)[1]
        if data_type == 'S1':
            target_data_pos = {'accels': [[0, 1, 2]],
                               'gyros': [[3, 4, 5]],
                               'temps': [[9]],
                               'angles': []
                               }
        elif data_type == 'S2':
            target_data_pos = {'accels': [[2, 3, 4]],
                               'gyros': [[5, 6, 7]],
                               'temps': [[8]],
                               'angles': []
                               }
        elif data_type == 'S3':
            x, y, z = 3, 3, -1
            target_data_pos = {'accels': [[4, 5, 6]],
                               'gyros': [[1, 2, 3]],
                               'temps': [[7]],
                               'angles': []
                               }
            packet_type_payload = self.pkt_info_dict[data_type][0]
        elif data_type == 'A1':
            target_data_pos = {'accels': [[6, 7, 8]],
                               'gyros': [[3, 4, 5]],
                               'temps': [[12]],
                               'angles': [[0, 1]]
                               }
        elif data_type == 'A2':
            target_data_pos = {'accels': [[6, 7, 8]],
                               'gyros': [[3, 4, 5]],
                               'temps': [[9]],
                               'angles': [[0, 1]]
                               }
        elif data_type == 'FM':
            chip_num = int((self.pkt_info_dict[data_type][1] - 11) / 28)
            if chip_num == 1:
                target_data_pos = {'accels': [[0, 1, 2]],
                                'gyros': [[3, 4, 5]],
                                'temps': [[6]],
                                'angles': []
                                }
            elif chip_num == 2:
                target_data_pos = {'accels': [[0, 1, 2], [7, 8, 9]],
                               'gyros': [[3, 4, 5], [10, 11, 12]],
                               'temps': [[6], [13]],
                               'angles': []
                                }
            elif chip_num == 3:
                target_data_pos = {'accels': [[0, 1, 2], [7, 8, 9], [14, 15, 16]],
                               'gyros': [[3, 4, 5], [10, 11, 12], [17, 18, 19]],
                               'temps': [[6], [13], [20]],
                               'angles': []
                                }
            elif chip_num == 4:
                target_data_pos = {'accels': [[0, 1, 2], [7, 8, 9], [14, 15, 16], [21, 22, 23]],
                               'gyros': [[3, 4, 5], [10, 11, 12], [17, 18, 19], [24, 25, 26]],
                               'temps': [[6], [13], [20], [27]],
                               'angles': []
                                }
        elif data_type == 'AT':
            x, y, z = 3, 3, -2
            target_data_pos = {'accels': [[3, 4, 5]],
                               'gyros': [[0, 1, 2]],
                               'temps': [[6]],
                               'angles': []
                               }
            packet_type_payload = self.pkt_info_dict[data_type][0]

        rev_thread = threading.Thread(target=self.rev_data_to_buffer, args=(bytes(packet_type_payload), data_length))
        rev_thread.start() 
        start_time = time.time()
        while self.isLog:
            if len(self.myqueue) != 0:
                data = self.myqueue.popleft()
                if data[:x] == bytes(packet_type_payload):
                    cnt += 1
                    if cnt == self.odr / idx:
                        payload = data[y:z]
                        if data_type == 'FM':
                            latest = parser(payload, chip_num)
                        else:
                            latest = parser(payload)
                        accels, gyros, temps, angles = [], [], [], []
                        for i, key in enumerate(target_data_pos):
                            if key == 'accels':
                                for lst in target_data_pos[key]:
                                    accels.append([latest[i] for i in lst]) 
                            elif key == 'gyros':
                                for lst in target_data_pos[key]:
                                    gyros.append([latest[i] for i in lst])
                            elif key == 'temps':
                                for lst in target_data_pos[key]:
                                    temps.append([latest[i] for i in lst])
                            elif key == 'angles':
                                for lst in target_data_pos[key]:
                                    angles.append([latest[i] for i in lst]) 
                        mylatest = [accels, gyros, temps, angles]
                        for lst in mylatest:
                            if len(lst) == 0:
                                mylatest.remove(lst)

                        '''data: np.array{[[[ax1, ay1, az1], [ax2, ay2, az2], [ax3, ay3, az3]],
                          [[gx1, gy1, gz1], [gx2, gy2, gz2], [gx3, gy3, gz3]],
                          [[t1],            [t2],            [t3]           ],
                          [[roll1, pitch1], [roll2, pitch2], [roll3, pitch3]]]}
                        '''
                        cnt = 0
                        start_time = time.time()
                        yield mylatest
                if time.time() - start_time > 3:
                    if self.isLog == True or retry_times != 0:
                        retry_times += 1
                        self.isLog = False
                        self.ser_close()
                        time.sleep(0.1)
                        self.ser_init()
                        rev_thread = threading.Thread(target=self.rev_data_to_buffer, args=(data_length,))
                        rev_thread.start() 
                if retry_times >= 3:
                    self.isLog = False
                    stdscr.addstr(2, 0, "Data visualization inital failed, Check your User Setting and try again")
            elif time.time() - start_time > 3:
                self.isLog = False
                stdscr.addstr(2, 0, "Data visualization inital failed, Check your User Setting and try again")