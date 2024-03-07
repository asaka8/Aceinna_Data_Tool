import os
import csv
import time
import struct
import serial

from ..communication.aceinna_uart import Uart
from ..front.data_visual import Visual
from ..front.setting_table import SettingTable

class IMUFunc:
    def __init__(self, com=None, baud=None, odr=None):
        if com != None:
            self.uut = Uart(com, baud, odr)
        else:
            self.uut = None
        self.packet_info = {
            'S1': ([0x55, 0x55, 0x53, 0x31], 31),
            'S2': ([0x55, 0x55, 0x53, 0x32], 45),
            'A1': ([0x55, 0x55, 0x41, 0X31], 39),
            'A2': ([0x55, 0x55, 0x41, 0x32], 37),
            'FM': ([0x55, 0x55, 0x46, 0x4D], 95),
            'a2': ([0x55, 0x55, 0x61, 0x32], 55),
            'S3': ([0x55, 0xAA, 0x24], 40),
            'AT': ([0xBD, 0XDB, 0x54], 39)
        }

        self.user_command = {
            'GP': [0x55, 0x55, 0x47, 0x50],
            'WF': [0x55, 0x55, 0x57, 0x46],
            'SF': [0x55, 0x55, 0x53, 0x46],
            'RF': [0x55, 0x55, 0x52, 0x46],
            'GF': [0x55, 0x55, 0x47, 0x46],
        }

    def get_imu_product_info(self):
        cmd = bytes(self.user_command['GP'])
        packet_payload = cmd
        packet_payload += bytes([0x02, 0x49, 0x44]) # length + 'ID'
        crc = bytes(self.calc_crc(packet_payload[2:]))
        packet = packet_payload + crc
        self.uut.ser_init()
        result = self.uut.write_read_response(packet)
        self.uut.ser_close()
        if result[0]:
            product_info_payload = result[1][5:-2]
            product_sn = struct.unpack('>I', product_info_payload[:4])[0]
            info_end_pos = product_info_payload.find(b'\x00')
            if info_end_pos != -1:
                product_info = product_info_payload[4:info_end_pos].decode('utf-8')
            else:
                product_info = product_info_payload[4:].decode('utf-8')
            product_info = f'{product_sn} ' + product_info
            return product_info
        return None

    def imu_data_record(self, data_type, logf_name, stdscr=None):
        try:
            self.uut.ser_init()
            self.uut.data_log(data_type, logf_name, stdscr)
            self.uut.ser_close()
        except serial.serialutil.SerialException as e:
            stdscr.addstr(6, 3, e.strerror)

    def imu_data_parse(self, data_path=None):
        data_file_name = data_path.split('\\')[-1] # get the file name
        data_type = data_file_name.split('_')[1] # get the packet type
        if data_type.find('.') != -1:
            data_type = data_type.split('.')[0]
        if data_type == 'S1':
            head_line = ['xAccel', 'yAccel', 'zAccel', 'xRate', 'yRate', 'zRate', 'xRateTemp', 'yRateTemp', 'zRateTemp', 'boardTemp', 'timer', 'BITstatus']
            for progress in self.parse_to_csvf(data_path, data_type, head_line):
                yield progress
        elif data_type == 'S2':
            head_line = ['gps_week', 'gps_time_of_week', 'x_accel', 'y_accel', 'z_accel', 'x_gyro', 'y_gyro', 'z_gyro', 'temp', 'master_bit']
            for progress in self.parse_to_csvf(data_path, data_type, head_line):
                yield progress
        elif data_type == 'S3':
            head_line = ['num', 'xRate', 'yRate', 'zRate', 'xAccel', 'yAccel', 'zAccel',  'boardTempCounts', 'supplierid', 'productid']
            for progress in self.parse_to_csvf_li(data_path, data_type, head_line):
                yield progress
        elif data_type == 'A1':
            head_line = ['rollAngle', 'pitchAngle', 'yawAngleMag', 'xRateCorrected', 'yRateCorrected', 'zRateCorrected', 'xAccel', 'yAccel', 'zAccel', 'xRateTemp', 'timeITOW', 'BITstatus']
            for progress in self.parse_to_csvf(data_path, data_type, head_line):
                yield progress
        elif data_type == 'A2':
            head_line = ['rollAngle', 'pitchAngle', 'yawAngleTrue', 'xRateCorrected', 'yRateCorrected', 'zRateCorrected', 'xAccel', 'yAccel', 'zAccel', 'xRateTemp', 'yRateTemp', 'zRateTemp', 'timeITOW', 'BITstatus']
            for progress in self.parse_to_csvf(data_path, data_type, head_line):
                yield progress
        elif data_type == 'FM':
            head_line = ['xAccelCounts1', 'yAccelCounts1', 'zAccelCounts1', 'xRateCounts1', 'yRateCounts1', 'zRateCounts1', 'TempCounts1', 'xAccelCounts2', 'yAccelCounts2', 'zAccelCounts2',
            'xRateCounts2', 'yRateCounts2', 'zRateCounts2', 'TempCounts2', 'xAccelCounts3', 'yAccelCounts3', 'zAccelCounts3', 'xRateCounts3', 'yRateCounts3', 'zRateCounts3', 'TempCounts3',
            'xAccelCounts4', 'yAccelCounts4', 'zAccelCounts4', 'xRateCounts4', 'yRateCounts4', 'zRateCounts4', 'TempCounts4', 'sensorSubset', 'sampleIdx']
            for progress in self.parse_to_csvf(data_path, data_type, head_line):
                yield progress
        elif data_type == 'AT':
            head_line = ['xRate', 'yRate', 'zRate', 'xAccel', 'yAccel', 'zAccel', 'Temp', 'Fixed value 0', 'Flags0', 'Flags1', 'Frame count', 'GPS Week', 'GPS TimeOfWeek', 'year', 'month',
            'day', 'hour', 'minute', 'second', 'milliseconds']
            for progress in self.parse_to_csvf_nio(data_path, data_type, head_line):
                yield progress

    def imu_data_visual(self, stdscr, data_type, maxt, dt):
        '''
        stdscr: curses ui
        data_type: The path of the data to be parsed
        maxt: Maximum time limit for data visualization
        dt: Update rate of data visualization
        '''
        self.uut.ser_init()
        self.uut.pkt_info_update(data_type)
        parser = eval(f'self.{data_type}_parse')
        emitter = self.uut.realtime_data
        if data_type == 'FM':
            data_length = self.uut.pkt_info_dict[data_type][1]
            chip_num = int((data_length - 11) / 28)
            vis = Visual(stdscr, data_type, maxt, dt, emitter, chip_num)
        else:
            vis = Visual(stdscr, data_type, maxt, dt, emitter)
        vis.start(parser)
        self.uut.isLog = False
        time.sleep(0.1)
        self.uut.ser_close()
    
    def imu_get_field_val(self, id_list):
        cmd = bytes(self.user_command['GF'])
        packet_payload = cmd
        packet = None
        user_info = {}

        num_fields = len(id_list)
        payload_length = num_fields * 2 + 1
        packet_payload += struct.pack('>B', payload_length)
        packet_payload += struct.pack('>B', num_fields)
        for id in id_list:
            packet_payload += struct.pack('>H', int(id))
        crc = bytes(self.calc_crc(packet_payload[2:]))
        packet = packet_payload + crc
        resp_length = num_fields * 4 + 1 + 7
        self.uut.ser_init()
        result = self.uut.write_read_response(packet, resp_length) # num + f0 + fv0 + f1 + fv1 ....
        if result[0] == True:
            resp_payload = result[1][5:-2]
            fmt = '>B'
            for i in range(num_fields):
                fmt += 'HH'
            value = struct.unpack(fmt, resp_payload)[1:]
            for i in range(len(value)):
                if i % 2 == 0:
                    user_info[value[i]] = hex(int(value[i+1]))[2:]
            self.uut.ser_close()
            return user_info
        self.uut.ser_close()
        return None

    def imu_read_field_val(self, id_list):
        cmd = bytes(self.user_command['RF'])
        packet_payload = cmd
        packet = None
        user_info = {}

        num_fields = len(id_list)
        payload_length = num_fields * 2 + 1
        packet_payload += struct.pack('>B', payload_length)
        packet_payload += struct.pack('>B', num_fields)
        for id in id_list:
            packet_payload += struct.pack('>H', int(id))
        crc = bytes(self.calc_crc(packet_payload[2:]))
        packet = packet_payload + crc
        resp_length = num_fields * 4 + 1 + 7
        self.uut.ser_init()
        result = self.uut.write_read_response(packet, resp_length) # num + f0 + fv0 + f1 + fv1 ....
        if result[0] == True:
            resp_payload = result[1][5:-2]
            fmt = '>B'
            for i in range(num_fields):
                fmt += 'HH'
            value = struct.unpack(fmt, resp_payload)[1:]
            for i in range(len(value)):
                if i % 2 == 0:
                    user_info[value[i]] = hex(int(value[i+1]))[2:]
            self.uut.ser_close()
            return user_info
        self.uut.ser_close()
        return None
        
    def imu_field_setting_temporary(self, stdscr, id_list, info=None):
        cmd = bytes(self.user_command['SF'])
        packet_payload = cmd
        packet = None
        table = SettingTable(info)
        modified_values = table.start(stdscr, id_list)
        if modified_values != None:
            num_fields = len(modified_values)
            payload_length = num_fields * 4 + 1
            packet_payload += struct.pack('>B', payload_length)
            packet_payload += struct.pack('>B', num_fields)
            for id in modified_values:
                if id != 3:
                    packet_payload += struct.pack('>H', id)
                    packet_payload += struct.pack('>H', int(modified_values[id], 16))
                else:
                    packet_payload += struct.pack('>H', id)
                    packet_payload += bytes.fromhex(modified_values[id])
            crc = bytes(self.calc_crc(packet_payload[2:]))
            packet = packet_payload + crc
        if packet is not None:
            self.uut.ser_init()
            resp_length = num_fields * 2 + 1 + 7
            result = self.uut.write_read_response(packet, resp_length)
            if result[0] == True:
                stdscr.addstr(2, 0, "Set fields successfully.")
                self.uut.ser_close()
                key = stdscr.getch()
                while key != ord('m') and key != ord('M'):
                    key = stdscr.getch()
            elif result[0] == False:
                stdscr.addstr(2, 0, "Set fields failed.")
                self.uut.ser_close()
                key = stdscr.getch()
                while key != ord('m') and key != ord('M'):
                    key = stdscr.getch()
            else:
                self.uut.ser_close()

    def imu_field_setting_permanent(self, stdscr, id_list, info=None):
        cmd = bytes(self.user_command['WF'])
        packet_payload = cmd
        packet = None
        table = SettingTable(info)
        modified_values = table.start(stdscr, id_list)
        if modified_values != None:
            num_fields = len(modified_values)
            payload_length = num_fields * 4 + 1
            packet_payload += struct.pack('>B', payload_length)
            packet_payload += struct.pack('>B', num_fields)
            for id in modified_values:
                if id != 3:
                    packet_payload += struct.pack('>H', id)
                    packet_payload += struct.pack('>H', int(modified_values[id], 16))
                else:
                    packet_payload += struct.pack('>H', id)
                    packet_payload += bytes.fromhex(modified_values[id])
            crc = bytes(self.calc_crc(packet_payload[2:]))
            packet = packet_payload + crc
        if packet is not None:
            self.uut.ser_init()
            resp_length = num_fields * 2 + 1 + 7
            result = self.uut.write_read_response(packet, resp_length)
            if result[0] == True:
                stdscr.addstr(2, 0, "Write fields successfully, please reboot device.")
                self.uut.ser_close()
                key = stdscr.getch()
                while key != ord('m') and key != ord('M'):
                    key = stdscr.getch()
            elif result[0] == False:
                stdscr.addstr(2, 0, "Write fields failed.")
                self.uut.ser_close()
                key = stdscr.getch()
                while key != ord('m') and key != ord('M'):
                    key = stdscr.getch()
            else:
                self.uut.ser_close()

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# subfunctions

    def parse_to_csvf(self, data_path, data_type, head_line):
        '''
        data_path: The path of the data to be parsed
        data_type: The type of the data to be parsed
        head_line: The header of the csv
        '''
        dataf = open(data_path, 'rb')
        data = dataf.read()
        packet_type_payload = bytes(self.packet_info[data_type][0])
        packet_length = self.packet_info[data_type][1]

        progress = 0
        progress_length = len(data)
        progress_step = packet_length

        with open(f'{data_path[:-4]}.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(head_line)
            head_line_length = len(head_line)
            progress = 0
            for i in range(len(data)):
                packet_msg = data[i: i+packet_length]
                packet_type_pos = packet_msg.find(packet_type_payload)
                if packet_type_pos == 0:
                    crc_check_payload = packet_msg[2: -2]
                    crc = packet_msg[-2:]
                    cal_crc = bytes(self.calc_crc(crc_check_payload))
                    if cal_crc != crc:
                        print('CRC ERROR!')
                    if len(packet_msg) == packet_length:
                        payload = packet_msg[5:-2]
                        latest = eval(f'self.{data_type}_parse')(payload)
                        data_line = [latest[i] for i in range(head_line_length)]
                        writer.writerow(data_line)
                        progress += (progress_step / progress_length) * 100
                        yield progress
    
    def parse_to_csvf_li(self, data_path, data_type, head_line):
        '''
        This function only for S3 packet

        data_path: The path of the data to be parsed
        data_type: The type of the data to be parsed
        head_line: The header of the csv
        '''
        dataf = open(data_path, 'rb')
        data = dataf.read()
        packet_type_payload = bytes(self.packet_info[data_type][0])
        packet_length = self.packet_info[data_type][1]

        progress = 0
        progress_length = len(data)
        progress_step = packet_length

        with open(f'{data_path[:-4]}.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(head_line)
            head_line_length = len(head_line)
            for i in range(len(data)):
                packet_msg = data[i: i+packet_length]
                packet_type_pos = packet_msg.find(packet_type_payload)
                if packet_type_pos == 0:
                    crc = packet_msg[-1]
                    cal_crc = sum(packet_msg[2: -1]) & 0xFF
                    if cal_crc != crc:
                        print('CRC ERROR!')
                    if len(packet_msg) == packet_length:
                        payload = packet_msg[3:-1]
                        latest = eval(f'self.{data_type}_parse')(payload)
                        data_line = [latest[i] for i in range(head_line_length)]
                        writer.writerow(data_line)
                        progress += (progress_step / progress_length) * 100
                        yield progress
    
    def parse_to_csvf_nio(self, data_path, data_type, head_line):
        '''
        This function only for AT packet

        data_path: The path of the data to be parsed
        data_type: The type of the data to be parsed
        head_line: The header of the csv
        '''
        dataf = open(data_path, 'rb')
        data = dataf.read()
        packet_type_payload = bytes(self.packet_info[data_type][0])
        packet_length = self.packet_info[data_type][1]

        progress = 0
        progress_length = len(data)
        progress_step = packet_length

        with open(f'{data_path[:-4]}.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(head_line)
            head_line_length = len(head_line)
            for i in range(len(data)):
                packet_msg = data[i: i+packet_length]
                packet_type_pos = packet_msg.find(packet_type_payload)
                if packet_type_pos == 0:
                    if len(packet_msg) == packet_length:
                        payload = packet_msg[3:-2]
                        latest = eval(f'self.{data_type}_parse')(payload)
                        data_line = [latest[i] for i in range(head_line_length)]
                        writer.writerow(data_line)
                        progress += (progress_step / progress_length) * 100
                        yield progress

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Parse functions

    def S1_parse(self, payload):
        fmt = '>hhhhhhhhhhHH'
        data = struct.unpack(fmt, payload)
        xAccel = data[0] * 20 / 2**16
        yAccel = data[1] * 20 / 2**16
        zAccel = data[2] * 20 / 2**16
        xRate = data[3] * 1260 / 2**16
        yRate = data[4] * 1260 / 2**16
        zRate = data[5] * 1260 / 2**16
        xRateTemp = data[6] * 200 / 2**16
        yRateTemp = data[7] * 200 / 2**16
        zRateTemp = data[8] * 200 / 2**16
        boardTemp = data[9] * 200 / 2**16
        timer = data[10] * 15.259022
        BITstatus = data[11]

        return xAccel, yAccel, zAccel, xRate, yRate, zRate, xRateTemp, yRateTemp, zRateTemp, boardTemp, timer, BITstatus

    def S2_parse(self, payload):
        gps_fmt = '<HI'
        fmt = '<fffffffI'
        gps_data = struct.unpack(gps_fmt, payload[:6])
        data = struct.unpack(fmt, payload[6:])
        gps_week = gps_data[0]
        gps_time_of_week = gps_data[1]
        x_accel = data[0]
        y_accel = data[1]
        z_accel = data[2]
        x_gyro = data[3]
        y_gyro = data[4]
        z_gyro = data[5]
        temp = data[6]
        master_bits = data[7]
        
        return gps_week, gps_time_of_week, x_accel, y_accel, z_accel, x_gyro, y_gyro, z_gyro, temp, master_bits

    def S3_parse(self, payload):
        fmt = '<I' + 'i'*6 + 'h' +'H'+'I'
        parse_data = struct.unpack(fmt, payload)
        num = parse_data[0]
        xRateCounts = parse_data[1]
        yRateCounts = parse_data[2]
        zRateCounts = parse_data[3]
        xAccelCounts = parse_data[4]
        yAccelCounts = parse_data[5]
        zAccelCounts = parse_data[6]
        systemp = parse_data[7]
        supplierid = parse_data[8]
        productid = parse_data[9]


        xAccel = round(xAccelCounts * 0.000001, 5) * 0.1
        yAccel = round(yAccelCounts * 0.000001, 5) * 0.1
        zAccel = round(zAccelCounts * 0.000001, 5) * 0.1
        xRate = round(xRateCounts * 0.000001, 5)
        yRate = round(yRateCounts * 0.000001, 5)
        zRate = round(zRateCounts * 0.000001, 5)
        boardTempCounts = round(systemp * 0.008, 3)

        return num,  xRate, yRate, zRate, xAccel, yAccel, zAccel,boardTempCounts, supplierid, productid

    def A1_parse(self, payload):
        fmt = '>hhhhhhhhhhhhhIH'
        parse_data = struct.unpack(fmt, payload)

        rollAngle = parse_data[0] * (360 / 2**16)
        pitchAngle = parse_data[1] * (360 / 2**16)
        yawAngle = parse_data[2] * (360 / 2**16)
        xRateCorrected = parse_data[3] * (1260 / 2**16)
        yRateCorrected = parse_data[4] * (1260 / 2**16)
        zRateCorrected = parse_data[5] * (1260 / 2**16)
        xAccel = parse_data[6] * (20 / 2**16)
        yAccel = parse_data[7] * (20 / 2**16)
        zAccel = parse_data[8] * (20 / 2**16)
        xMag = parse_data[9] * (2 / 2**16)
        yMag = parse_data[10] * (2 / 2**16)
        zMag = parse_data[11] * (2 / 2**16)
        xRateTemp = parse_data[12] * (200 / 2**16)
        timeITOW = parse_data[13]
        BITstatus = parse_data[14]

        return rollAngle, pitchAngle, yawAngle, xRateCorrected, yRateCorrected, zRateCorrected, xAccel, yAccel, zAccel, xMag, yMag, zMag, xRateTemp, timeITOW, BITstatus

    def A2_parse(self, payload):
        fmt = '>hhhhhhhhhhhhIH'
        parse_data = struct.unpack(fmt, payload)
        rollAngle = parse_data[0] * (360 / 2**16)
        pitchAngle = parse_data[1] * (360 / 2**16)
        yawAngle = parse_data[2] * (360 / 2**16)
        xRateCorrected = parse_data[3] * (1260 / 2**16)
        yRateCorrected = parse_data[4] * (1260 / 2**16)
        zRateCorrected = parse_data[5] * (1260 / 2**16)
        xAccel = parse_data[6] * (20 / 2**16)
        yAccel = parse_data[7] * (20 / 2**16)
        zAccel = parse_data[8] * (20 / 2**16)
        xRateTemp = parse_data[9] * (200 / 2**16)
        yRateTemp = parse_data[10] * (200 / 2**16)
        zRateTemp = parse_data[11] * (200 / 2**16)
        timeITOW = parse_data[12]
        BITstatus = parse_data[13]
        return rollAngle, pitchAngle, yawAngle, xRateCorrected, yRateCorrected, zRateCorrected, xAccel, yAccel, zAccel, xRateTemp, yRateTemp, zRateTemp, timeITOW, BITstatus

    def FM_parse(self, payload, chip_num):
        if len(payload) > (chip_num * 28) + 4:
            fmt = '<' + 'i'*chip_num*7 + 'H'*3
        else:
            fmt = '<' + 'i'*chip_num*7 + 'H'*2
        parse_data = struct.unpack(fmt, payload)

        return parse_data

    def AT_parse(self, payload):
        fmt = '<hhhhhhhBBBHHIHBBBBBH'
        parse_data = struct.unpack(fmt, payload)
        xRate = parse_data[0] * (300/32768)
        yRate = parse_data[1] * (300/32768)
        zRate = parse_data[2] * (300/32768)
        xAccel = parse_data[3] * (12/32768)
        yAccel = parse_data[4] * (12/32768)
        zAccel = parse_data[5] * (12/32768)
        Temp = parse_data[6] * (200.0/32768)
        FixVal = parse_data[7]
        Flags0 = parse_data[8]
        Flags1 = parse_data[9]
        FramCounts = parse_data[10]
        GpsWeek = parse_data[11]
        TimeOfWeek = parse_data[12] * (1E-03)
        year = parse_data[13]
        month = parse_data[14]
        day = parse_data[15]
        hour = parse_data[16]
        minute = parse_data[17]
        second = parse_data[18]
        milliseconds = parse_data[19]

        return  xRate, yRate, zRate, xAccel, yAccel, zAccel, Temp, FixVal, Flags0, Flags1, FramCounts, GpsWeek, TimeOfWeek, year, month, day, hour, minute, second, milliseconds

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# calculate crc

    def calc_crc(self, payload):
        '''
        Calculates 16-bit CRC-CCITT
        '''
        crc = 0x1D0F
        for bytedata in payload:
            crc = crc ^ (bytedata << 8)
            i = 0
            while i < 8:
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                i += 1

        crc = crc & 0xffff
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        return [crc_msb, crc_lsb]