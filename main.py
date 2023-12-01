import sys
from src.front.main_ui import Front

sys.dont_write_bytecode = True

if __name__ == '__main__':
    f = Front()
    f.start()
