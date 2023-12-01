import time
import threading
import collections
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from matplotlib.lines import Line2D
from collections import deque

class Scope:
    def __init__(self, ax1, ax2, ax3=None, maxt=5, dt=0.02):
        '''
        ax1, ax2: Graphic object
        maxt: Maximum time limit for data visualization
        dt: Update rate of data visualization
        '''
        self.ax_a = ax1
        self.ax_g = ax2
        self.dt = dt
        self.maxt = maxt
        self.tdata = deque([0], maxlen=int(maxt/dt))
        self.accel_data = deque([np.zeros(3)], maxlen=int(maxt/dt))
        self.gyro_data = deque([np.zeros(3)], maxlen=int(maxt/dt))


        self.line_ax = Line2D([], [], color='red')
        self.line_ay = Line2D([], [], color='blue')
        self.line_az = Line2D([], [], color='green')
        self.line_gx = Line2D([], [], color='red')
        self.line_gy = Line2D([], [], color='blue')
        self.line_gz = Line2D([], [], color='green')
        
        self.ax_a.add_line(self.line_ax)
        self.ax_a.add_line(self.line_ay)
        self.ax_a.add_line(self.line_az)
        self.ax_g.add_line(self.line_gx)
        self.ax_g.add_line(self.line_gy)
        self.ax_g.add_line(self.line_gz)
        
        self.ax_a.set_ylim(-8, 8)
        self.ax_g.set_ylim(-360, 360)
        self.ax_a.set_xlim(0, self.maxt)
        self.ax_g.set_xlim(0, self.maxt)

        self.ax_a.legend(['accelx', 'accely', 'accelz'], loc='upper right')
        self.ax_g.legend(['gyrox', 'gyroy', 'gyroz'], loc='upper right')

        if ax3 is not None:
            self.ax_ang = ax3
            self.angle_data = deque([np.zeros(2)], maxlen=int(maxt/dt))
            self.line_angr = Line2D([], [], color='red')
            self.line_angp = Line2D([], [], color='blue')
            self.ax_ang.add_line(self.line_angr)
            self.ax_ang.add_line(self.line_angp)
            self.ax_ang.set_ylim(-180, 180)
            self.ax_ang.set_xlim(0, self.maxt)
            self.ax_ang.legend(['roll', 'pitch'], loc='upper right')


    def update(self, data):
        ax, ay, az, gx, gy, gz = data
        lastt = self.tdata[-1] + self.dt
        self.tdata.append(lastt)
        self.accel_data.append(np.array([ax, ay, az]))
        self.gyro_data.append(np.array([gx, gy, gz]))

        accel_data = np.array(self.accel_data)
        gyro_data = np.array(self.gyro_data)

        self.line_ax.set_data(self.tdata, accel_data[:, 0])
        self.line_ay.set_data(self.tdata, accel_data[:, 1])
        self.line_az.set_data(self.tdata, accel_data[:, 2])
        self.line_gx.set_data(self.tdata, gyro_data[:, 0])
        self.line_gy.set_data(self.tdata, gyro_data[:, 1])
        self.line_gz.set_data(self.tdata, gyro_data[:, 2])

        self.ax_a.set_xlim(self.tdata[0], lastt)
        self.ax_g.set_xlim(self.tdata[0], lastt)

        return self.line_ax, self.line_ay, self.line_az, self.line_gx, self.line_gy, self.line_gz

    def update_(self, data):
        ax, ay, az, gx, gy, gz, roll, pitch = data
        lastt = self.tdata[-1] + self.dt
        self.tdata.append(lastt)
        self.accel_data.append(np.array([ax, ay, az]))
        self.gyro_data.append(np.array([gx, gy, gz]))
        self.angle_data.append(np.array([roll, pitch]))

        accel_data = np.array(self.accel_data)
        gyro_data = np.array(self.gyro_data)
        angle_data = np.array(self.angle_data)

        self.line_ax.set_data(self.tdata, accel_data[:, 0])
        self.line_ay.set_data(self.tdata, accel_data[:, 1])
        self.line_az.set_data(self.tdata, accel_data[:, 2])
        self.line_gx.set_data(self.tdata, gyro_data[:, 0])
        self.line_gy.set_data(self.tdata, gyro_data[:, 1])
        self.line_gz.set_data(self.tdata, gyro_data[:, 2])
        self.line_angr.set_data(self.tdata, angle_data[:, 0])
        self.line_angp.set_data(self.tdata, angle_data[:, 1])

        self.ax_a.set_xlim(self.tdata[0], lastt)
        self.ax_g.set_xlim(self.tdata[0], lastt)
        self.ax_ang.set_xlim(self.tdata[0], lastt)

        return self.line_ax, self.line_ay, self.line_az, self.line_gx, self.line_gy, self.line_gz, self.line_angr, self.line_angp

class Visual:
    def __init__(self, stdscr, data_type, maxt, dt, emitter=None):
        self.data_type = data_type
        if data_type == 'A2':
            self.fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
            self.scope = Scope(ax1, ax2, ax3, maxt, dt)
        else:
            self.fig, (ax1, ax2) = plt.subplots(2, 1)
            self.scope = Scope(ax1, ax2, maxt=maxt, dt=dt)
        
        if emitter is None:
            self.emitter = self.emitter_
        else:
            self.emitter = emitter
        
        self.myqueue = deque(maxlen=1000000)
        
        self.stdscr = stdscr

    def emitter_(self):
        while True:
            v1 = np.random.rand()
            v2 = np.random.rand()
            v3 = 0.3
            v4 = 12
            v5 = 12
            v6 = 12
            yield v1, v2, v3, v4, v5, v6

    def start(self, parser):
        if self.data_type == 'A2':
            update = self.scope.update_
        else:
            update = self.scope.update
        ani = animation.FuncAnimation(
            self.fig,
            update, 
            self.emitter(self.stdscr, self.data_type, parser),
            interval=10, 
            blit=True, 
            cache_frame_data=False
            )
        plt.show()
