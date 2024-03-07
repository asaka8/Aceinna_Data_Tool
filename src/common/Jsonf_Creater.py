import os
import json
import struct

JSON_DATA = {
    "myUart": {
        'port name': 'COM25',
        'baud rate': 230400,
        'output rate': 100
    },
    "myPacket": {
        'device type': 'IMU330BA',
        'packet type': 'S1'
    },
    "myVisual": {
        'maxt': 10,
        'dt': 0.02,
    }
}

class JsonCreate:
    def __init__(self) -> None:
        self.script_dir = os.path.dirname(__file__)

    def create(self, p=None):
        setting_dir = os.path.join('./setting')
        if not os.path.exists(setting_dir):
            os.mkdir(setting_dir)
        json_dir = os.path.join(f'./setting/params_setting.json')
        if p != None:
            json.dump(p, open(json_dir, 'w'), indent=4)
        if not os.path.exists(json_dir):     
            json.dump(JSON_DATA, open(json_dir, 'w'), indent=4)
            with open(json_dir) as json_file:
                properties = json.load(json_file)
        else:
            with open(json_dir) as json_file:
                properties = json.load(json_file)
        return properties

        