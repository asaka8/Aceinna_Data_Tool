import main
import cProfile

cProfile.run('main.Front().start()')


def main(x):
    odr = x
    if odr == 200:
        idx = 20
    elif odr == 100:
        idx = 20
    elif odr == 50:
        idx = 2
    elif odr == 20: 
        idx = 1
    elif odr == 10:
        idx = 1