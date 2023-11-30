import sys
import serial
import time

from ..communication.aceinna_uart import Uart

LOCKEEPROM = [0x4c, 0x45]
LOCKAPP = [0x4c, 0x41]
LOCKBOOT = [0x4c, 0x42]

UNLOCKEEPROM = [0x55, 0x45]
UNLOCKAPP = [0x55, 0x41]
UNLOCKBOOT = [0x55, 0x42]

UNLOCKPAYLOAD = [0x92, 0x33, 0x62, 0x19, 0x64, 0x27, 0x42, 0x85]

class IMU330BA:
    ############## Private Methods ###############
    def __init__(self, com, baud, odr, fpath):
        self.uart = Uart(com, baud, odr)
        self.UUT = None
        self.filename = fpath
        self.boot = 0

    def calc_crc(self, payload):
        '''Calculates CRC per 380 manual
        '''
        crc = 0x1D0F
        for bytedata in payload:
            crc = crc ^ (bytedata << 8)
            for i in range(0, 8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1

        crc = crc & 0xffff
        return crc

    def build_content(self, content):
        len_mod = len(content) % 16
        if len_mod == 0:
            return content

        fill_bytes = bytes(16 - len_mod)
        return content + fill_bytes

    def restart_device(self):
        self.set_quiet()
        C = [0x55, 0x55] + [0x53, 0x52] + [0x00]
        crc = self.calc_crc(C[2:4] + [0x00])
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        C.insert(len(C), crc_msb)
        C.insert(len(C), crc_lsb)
        self.UUT.reset_input_buffer()
        self.UUT.write(C)
        # grab with header, type, length, and crc
        R = self.UUT.read(7)
        if R[0] == 85 and R[1] == 85:
            self.packet_type = '{0:1c}'.format(R[2]) + '{0:1c}'.format(R[3])
            if self.packet_type == 'SR':
                return True
            else:
                return False
        return False

    def parse_packet(self, payload, ws=False):

        if self.packet_type == 'ID':
            sn = int(payload[0] << 24) + int(payload[1] << 16) + \
                 int(payload[2] << 8) + int(payload[3])
            return '{0} {1}'.format(sn, payload[4:].decode())
        elif self.packet_type == 'GF':
            n = payload[0]
            data = [0] * n  # empty array
            for i in range(n):
                # remap about odr because unit was forced to quiet mode during GF read
                if ((256 * payload[i * 4 + 1] + payload[i * 4 + 2]) == 1):
                    payload[i * 4 + 3] = 0
                    payload[i * 4 + 4] = self.odr_setting
                if ws == False:
                    print(('Get Field: 0x{0:02X}'.format(payload[i * 4 + 1]) + '{0:02X}'.format(payload[i * 4 + 2])
                           + ' set to: 0x{0:02X}{1:02X}'.format(payload[i * 4 + 3], payload[i * 4 + 4])
                           + ' ({0:1c}{1:1c})'.format(payload[i * 4 + 3], payload[i * 4 + 4])))
                else:
                    data[i] = [256 * payload[i * 4 + 1] + payload[i * 4 + 2],
                               256 * payload[i * 4 + 3] + payload[i * 4 + 4]]
            return data

    def lock(self, packet_type):
        if packet_type != [0x4c, 0x45]:
            self.baudrate = 115200
        self.set_quiet()
        C = [0x55, 0x55] + packet_type + [0x00]
        crc = self.calc_crc(C[2:4] + [0x00])
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        C.insert(len(C), crc_msb)
        C.insert(len(C), crc_lsb)
        self.UUT.reset_input_buffer()
        self.UUT.write(C)
        # grab with header, type, length, and crc
        R = self.UUT.read(7)
        self.UUT.reset_input_buffer()

    def unlock(self, packet_type, payload):
        str_packet_type = chr(packet_type[0]) + chr(packet_type[1])
        if str_packet_type == 'LE':
            self.baudrate = 115200
        else:
            self.baudrate = 230400
        self.set_quiet()
        C = [0x55, 0x55] + packet_type + [len(payload)] + payload
        crc = self.calc_crc(C[2:C[4] + 5])
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        C.insert(len(C), crc_msb)
        C.insert(len(C), crc_lsb)
        self.UUT.reset_input_buffer()
        self.UUT.write(C)
        # grab with header, type, length, and crc
        R = self.UUT.read(7)
        self.UUT.reset_input_buffer()
        if R[0] == 85 and R[1] == 85:
            self.packet_type = '{0:1c}'.format(R[2]) + '{0:1c}'.format(R[3])
            if self.packet_type == 'UE':
                return True
            elif self.packet_type == 'UA':
                return True
            elif self.packet_type == 'UB':
                return True
            else:
                return False
        else:
            return False

    def set_quiet(self):
        time.sleep(0.1)  # wait for any packets to clear
        C = [0x55, 0x55, ord('S'), ord('F'), 0x05, 0x01,
             0x00, 0x01, 0x00, 0x00]
        crc = self.calc_crc(C[2:C[4] + 5])
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        C.insert(len(C), crc_msb)
        C.insert(len(C), crc_lsb)

        self.UUT.reset_input_buffer()
        self.UUT.write(C)
        self.UUT.read(10)
        time.sleep(0.1)  # wait for command to take effect
        self.UUT.reset_input_buffer()

    def get_id_str(self):
        ''' Executes GP command and requests ID data from 380
            :returns:
                id string of connected device, or false if failed
        '''
        self.set_quiet()
        C = [0x55, 0x55, ord('G'), ord('P'), 0x02, ord('I'), ord('D')]
        crc = self.calc_crc(C[2:C[4] + 5])
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        C.insert(len(C), crc_msb)
        C.insert(len(C), crc_lsb)
        self.UUT.write(C)
        R = self.UUT.read(5)
        if len(R) and R[0] == 85 and R[1] == 85:
            self.packet_type = '{0:1c}'.format(R[2]) + '{0:1c}'.format(R[3])
            payload_length = R[4]
            R = self.UUT.read(payload_length + 2)
            id_str = self.parse_packet(R[0:payload_length])
            self.ID = id_str
            if id_str.find('load') == -1:
                self.boot = 0
            else:
                self.boot = 1
            return id_str
        else:
            return False

    def start_bootloader(self):
        '''Starts bootloader
            :returns:
                True if bootloader mode entered, False if failed
        '''
        self.UUT.baudrate = 230400
        self.set_quiet()
        time.sleep(2)
        C = [0x55, 0x55, ord('J'), ord('I'), 0x00]
        # for some reason must add a payload byte to get correct CRC
        crc = self.calc_crc(C[2:4] + [0x00])
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        C.insert(len(C), crc_msb)
        C.insert(len(C), crc_lsb)
        self.UUT.write(C)
        time.sleep(2)  # must wait for boot loader to be ready
        R = self.UUT.read(5)
        if R[0] == 85 and R[1] == 85:
            self.packet_type = '{0:1c}'.format(R[2]) + '{0:1c}'.format(R[3])
            if self.packet_type == 'JI':
                self.UUT.read(R[4] + 2)
                time.sleep(2)
                self.UUT.reset_input_buffer()
                #                    self.find_device()
                #                    self.reset_buffer()
                return True
            else:
                return False
        else:
            return False

    def get_protection_status(self, fields, ws=False):
        '''
        get protection status
        '''
        self.set_quiet()
        num_fields = len(fields)
        C = [0x55, 0x55, ord('G'), ord('F'), num_fields * 2 + 1, num_fields]
        for field in fields:
            field_msb = (field & 0xFF00) >> 8
            field_lsb = field & 0x00FF
            C.insert(len(C), field_msb)
            C.insert(len(C), field_lsb)
        crc = self.calc_crc(C[2:C[4] + 5])
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        C.insert(len(C), crc_msb)
        C.insert(len(C), crc_lsb)
        self.UUT.write(C)
        R = self.UUT.read(num_fields * 4 + 1 + 7)
        data = []
        if R and R[0] == 85 and R[1] == 85:
            # crc is last two bytes
            packet_crc = 256 * R[-2] + R[-1]
            calc_crc = self.calc_crc(R[2:R[4] + 5])
            if packet_crc == calc_crc:
                self.packet_type = '{0:1c}'.format(
                    R[2]) + '{0:1c}'.format(R[3])
                data = self.parse_packet(R[5:R[4] + 5])
        return data

    def start_app(self):
        '''Starts app
        '''
        # self.set_quiet()
        C = [0x55, 0x55, ord('J'), ord('A'), 0x00]
        # for some reason must add a payload byte to get correct CRC
        crc = self.calc_crc(C[2:4] + [0x00])
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        C.insert(len(C), crc_msb)
        C.insert(len(C), crc_lsb)
        self.UUT.write(C)
        time.sleep(1)
        R = self.UUT.read(7)
        if R[0] == 85 and R[1] == 85:
            self.packet_type = '{0:1c}'.format(R[2]) + '{0:1c}'.format(R[3])

    def write_block(self, buf, data_len, addr):
        '''Executed WA command to write a block of new app code into memory
        '''
        C = [0x55, 0x55, ord('W'), ord('A'), data_len + 5]
        addr_3 = (addr & 0xFF000000) >> 24
        addr_2 = (addr & 0x00FF0000) >> 16
        addr_1 = (addr & 0x0000FF00) >> 8
        addr_0 = (addr & 0x000000FF)
        C.insert(len(C), addr_3)
        C.insert(len(C), addr_2)
        C.insert(len(C), addr_1)
        C.insert(len(C), addr_0)
        C.insert(len(C), data_len)
        for i in range(data_len):
            C.insert(len(C), buf[i])
        crc = self.calc_crc(C[2:C[4] + 5])
        crc_msb = int((crc & 0xFF00) >> 8)
        crc_lsb = int((crc & 0x00FF))
        C.insert(len(C), crc_msb)
        C.insert(len(C), crc_lsb)
        status = 0
        self.UUT.baudrate = 57600
        while status == 0:
            self.UUT.write(C)
            if addr == 0:
                time.sleep(26)
            else:
                time.sleep(0.1)
            R = self.UUT.read(12)  # longer response
            if len(R) > 1 and R[0] == 85 and R[1] == 85:
                self.packet_type = '{0:1c}'.format(
                    R[2]) + '{0:1c}'.format(R[3])
                if self.packet_type == 'WA':
                    status = 1
                else:
                    sys.exit()
                    status = 0
            else:
                self.UUT.reset_input_buffer()
                time.sleep(1)
                sys.exit()

    def upgrade_fw(self):
        '''Upgrades firmware of connected 380 device to file provided in argument
        '''
        max_data_len = 192
        write_len = 0
        fw = open(self.filename, 'rb').read()
        fw = self.build_content(fw)
        fs_len = len(fw)

        progress = 0

        time.sleep(1)
        while write_len < fs_len:
            packet_data_len = max_data_len if (fs_len - write_len) > max_data_len else (fs_len - write_len)
            # From IMUView
            write_buf = fw[write_len:(write_len + packet_data_len)]
            self.write_block(write_buf, packet_data_len, write_len)
            write_len += packet_data_len
            progress += (max_data_len / fs_len) * 100
            yield progress
            
