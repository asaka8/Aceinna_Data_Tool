import os
import sys
import time
import curses
import argparse
import subprocess

from ..communication.aceinna_uart import Uart
from ..common.Jsonf_Creater import JsonCreat
from ..functions.imu_func import IMUFunc
from ..functions.imu_upgrade import IMU330BA
from .progress_bar import progress_bar

class Front:
    def __init__(self):
        self.jsonf = JsonCreat()
        self.stdscr = None

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def display_menu(self, stdscr, menu_items, current_row):
        stdscr.clear()
        for idx, item in enumerate(menu_items):
            x = 0
            y = idx
            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, item)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, item)
        stdscr.refresh()

    def process_menu_input(self, stdscr, menu_items, current_row):
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            return current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            return current_row + 1
        elif key in [curses.KEY_ENTER, 10, 9+len(menu_items)]:
            return -1
        return current_row

    def main_menu(self, stdscr):
        curses.curs_set(0)
        stdscr.clear()
        stdscr.refresh()

        menu_items = ["Data Log", "Data Parse", "Data Visual", "FW Upgrade", "Exit"]
        current_row = 0

        while True:
            self.display_menu(stdscr, menu_items, current_row)
            choice = self.process_menu_input(stdscr, menu_items, current_row)
            if choice == -1:
                if current_row == 0:  # Data log
                    self.data_log(stdscr)
                elif current_row == 1:  # Data parse
                    self.data_parse(stdscr)
                elif current_row == 2: # Data visual
                    self.data_visual(stdscr)
                elif current_row == 3: # FW Upgrade
                    self.fw_upgrade(stdscr)
                elif current_row == 4:  # Exit
                    break
            else:
                current_row = choice
        sys.exit(0)
    
    def main(self, stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_WHITE)
        self.main_menu(stdscr)

    def count_used_rows(self, stdscr):
        rows, cols = os.get_terminal_size()

        used_rows = 0
        for y in range(rows):
            line = stdscr.instr(y, 0).decode('utf-8').strip()
            if line:
                used_rows += 1

        return used_rows

    def start(self):
        curses.wrapper(self.main)
        
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def data_log(self, stdscr):
        menu_items = ["Start Log", "User Setting", "Back"]
        current_row = 0
        is_running = True

        while is_running:
            self.display_menu(stdscr, menu_items, current_row)
            choice = self.process_menu_input(stdscr, menu_items, current_row)
            if choice == -1:  # the value '-1' means user made a choice
                if current_row == 0:  # Start Log
                    properties = self.jsonf.creat()
                    self.start_log(stdscr, p=properties)
                elif current_row == 1:  # Serial Setting
                    self.settings(stdscr)
                elif current_row == 2:  # Back
                    is_running = False
            else:
                current_row = choice
    
    def data_parse(self, stdscr):
        stdscr.clear()
        stdscr.refresh()
        self.stdscr = stdscr
        
        current_path = os.getcwd()
        data_path = os.path.join(current_path, "data")
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        file_list, file_dict = self.data_folder_manager()

        menu_items = file_list + ['Data Folder'] + ['Back']
        current_row = 0
        is_running = True

        while is_running:
            self.display_menu(stdscr, menu_items, current_row)
            choice = self.process_menu_input(stdscr, menu_items, current_row)
            if choice == -1:
                selected_item = menu_items[current_row]
                if selected_item == 'Data Folder':
                    self.open_data_folder(stdscr)
                elif selected_item == 'Back':
                    is_running = False
                else:
                    file_path = file_dict[selected_item]
                    self.parse(stdscr, file_path)
            else:
                current_row = choice

    def data_visual(self, stdscr):
        menu_items = ["Play Data", "Serial Setting", "Back"]
        current_row = 0
        is_running = True

        while is_running:
            self.display_menu(stdscr, menu_items, current_row)
            choice = self.process_menu_input(stdscr, menu_items, current_row)
            if choice == -1:  # the value '-1' means user made a choice
                if current_row == 0:  # Play
                    properties = self.jsonf.creat()
                    self.visual(stdscr, p=properties)
                elif current_row == 1:  # Serial Setting
                    self.settings(stdscr)
                elif current_row == 2:  # Back
                    is_running = False
            else:
                current_row = choice

    def fw_upgrade(self, stdscr):
        stdscr.clear()
        stdscr.refresh()
        self.stdscr = stdscr

        current_path = os.getcwd()
        data_path = os.path.join(current_path, "bin")
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        file_list, file_dict = self.fw_folder_manager()

        menu_items = file_list + ['FW Folder'] + ['Back']
        current_row = 0
        is_running = True

        while is_running:
            self.display_menu(stdscr, menu_items, current_row)
            choice = self.process_menu_input(stdscr, menu_items, current_row)
            if choice == -1:
                selected_item = menu_items[current_row]
                if selected_item == 'FW Folder':
                    self.open_fw_folder(stdscr)
                elif selected_item == 'Back':
                    is_running = False
                else:
                    file_path = file_dict[selected_item]
                    properties = self.jsonf.creat()
                    self.upgrade(stdscr, properties, file_path)
            else:
                current_row = choice

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# subfunction of 'self.data_log'
    def start_log(self, stdscr, p):
        stdscr.clear()
        stdscr.refresh()
        stdscr.addstr(0, 0, "Press 'Enter' to start log, or press 'M' to Exit.")
        com = p['myUart']['port name']
        baud = p['myUart']['baud rate']
        odr = p['myUart']['output rate']
        logFlag = False
        key = stdscr.getch()
        time_stamp = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
        device_type = p['myPackets']['device type']
        packet_type = p['myPackets']['packet type']
        path = f".\data\{device_type}_{packet_type}_{time_stamp}.bin"
        while key != ord('m'):
            if logFlag == False:
                imu_func = IMUFunc(com, baud, odr)
                imu_func.imu_data_record(data_type=packet_type, logf_name=path, stdscr=stdscr)
                logFlag = True
            key = stdscr.getch()

    def settings(self, stdscr):
        stdscr.clear()
        stdscr.addstr(0, 0, "Press 'Enter' to set parameters, or press 'M' to Exit.")
        stdscr.refresh()
        key = stdscr.getch()
        p = self.jsonf.creat()
        file_path = (f'.\setting\params_setting.json')
        while key != ord('m'):
            try:
                subprocess.run(['notepad', file_path])
            except OSError as e:
                stdscr.addstr(3, 0, f"{e}")
            key = stdscr.getch()

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# subfunction of 'self.data_parse'
    def data_folder_manager(self):
        folder_path =  '.\\data'
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if f[-3:] == 'bin':
                    file_list.append(f)
            root = root
        file_dict = {}
        for f in file_list:
            if f[-3:] == 'bin':
                file_dict.update({f: os.path.join(root, f)})
        return file_list, file_dict

    @progress_bar(step=0, length=100)
    def parse(self, stdscr, file_path):
        imu_func = IMUFunc()
        for progress in imu_func.imu_data_parse(file_path):
            yield progress
        # stdscr.addstr(5, 0, "data parse finished")

    def open_data_folder(self, stdscr):
        current_path = os.getcwd()
        data_path = os.path.join(current_path, "data")
        if os.path.exists(data_path):
            os.startfile(data_path)     
        else:
            stdscr.addstr(6, 0, "data folder not found")

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# subfunction of 'self.data_visual'
    def visual(self, stdscr, p):
        stdscr.clear()
        stdscr.refresh()
        stdscr.addstr(0, 0, "Press 'Enter' to start log, or press 'M' to Exit.")
        com = p["myUart"]['port name']
        baud = p["myUart"]['baud rate']
        odr = p["myUart"]['output rate']
        maxt = p["myVisual"]['maxt']
        dt = p["myVisual"]['dt']
        visualFlag = False
        key = stdscr.getch()
        device_type = p['myPackets']['device type']
        packet_type = p['myPackets']['packet type']
        while key != ord('m'):
            if visualFlag == False:
                imu_func = IMUFunc(com, baud, odr)
                imu_func.imu_data_visual(stdscr=stdscr, data_type=packet_type, maxt=maxt, dt=dt)
                visualFlag = True
            key = stdscr.getch()

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# subfunction of 'self.fw_upgrade'
    def fw_folder_manager(self):
        folder_path =  '.\\bin'
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if f[-3:] == 'bin':
                    file_list.append(f)
            root = root
        file_dict = {}
        for f in file_list:
            if f[-3:] == 'bin':
                file_dict.update({f: os.path.join(root, f)})
        return file_list, file_dict

    @progress_bar(step=0, length=100)
    def upgrade(self, stdscr, p, fpath):
        row_num = self.count_used_rows(stdscr)
        com = p["myUart"]['port name']
        baud = p["myUart"]['baud rate']
        odr = p["myUart"]['output rate']
        
        unit = IMU330BA(com, baud, odr, fpath)
        unit.uart.ser_init()
        unit.UUT = unit.uart.ser
        sb_res = unit.start_bootloader()
        if sb_res:
            for progress in unit.upgrade_fw():
                yield progress
            time.sleep(1)
            unit.start_app()
            stdscr.addstr(row_num+1, 0, "upgrade finished, please reboot device.")
            unit.uart.ser_close()
        else:
            stdscr.addstr(row_num+1, 0, "jump to bootloader failed, please check.")

    def open_fw_folder(self, stdscr):
        current_path = os.getcwd()
        bin_path = os.path.join(current_path, "bin")
        if os.path.exists(bin_path):
            os.startfile(bin_path)     
        else:
            stdscr.addstr(6, 0, "data folder not found")
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    f = Front()
    f.start()