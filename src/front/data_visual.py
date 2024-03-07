import time
import threading
import collections
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from matplotlib.lines import Line2D
from collections import deque

class Scope:
    def __init__(self, axs, maxt=5, dt=0.02, data_type=None):
        '''
        axs: Graphic object
        4xn
             array{[ax1, ax2, ..., axn],
                   [gx1, gx2, ..., gxn],
                   [t1,  t2,  ..., tn],
                   [ang1, ang2, ..., angn]}
        maxt: Maximum time limit for data visualization
        dt: Update rate of data visualization
        '''
        self.data_type = data_type
        self.dt = dt
        self.maxt = maxt
        self.tdata = deque([0], maxlen=int(maxt/dt))
        self.axs_stats = {}
        self.axs = axs
        for i, axs_row in enumerate(self.axs):
            if not isinstance(axs_row, np.ndarray):
                axs_row = np.array([axs_row])
            for j in range(len(axs_row)):
                ax = axs_row[j]
                if i == 0: # accels
                    accel_data = deque([np.zeros(3)], maxlen=int(maxt/dt))
                    line_ax = Line2D([], [], color='red')
                    line_ay = Line2D([], [], color='blue')
                    line_az = Line2D([], [], color='green')
                    ax.add_line(line_ax)
                    ax.add_line(line_ay)
                    ax.add_line(line_az)
                    if data_type == 'FM':
                        ax.set_ylim(-40000, 40000)
                    else:
                        ax.set_ylim(-8, 8)
                    ax.set_xlim(0, self.maxt)
                    atext = ax.text(0.01, 0.85, '', transform=ax.transAxes)
                    ax.legend(['accelx', 'accely', 'accelz'], loc='upper right')
                    self.axs_stats[(i, j)] = [accel_data, atext, [line_ax, line_ay, line_az]]
                elif i == 1: # gyros
                    gyro_data = deque([np.zeros(3)], maxlen=int(maxt/dt))
                    line_gx = Line2D([], [], color='red')
                    line_gy = Line2D([], [], color='blue')
                    line_gz = Line2D([], [], color='green')
                    ax.add_line(line_gx)
                    ax.add_line(line_gy)
                    ax.add_line(line_gz)
                    if data_type == 'FM':
                        ax.set_ylim(-40000, 40000)
                    else:
                        ax.set_ylim(-360, 360)
                    ax.set_xlim(0, self.maxt)
                    gtext = ax.text(0.01, 0.85, '', transform=ax.transAxes)
                    ax.legend(['gyrox', 'gyroy', 'gyroz'], loc='upper right')
                    self.axs_stats[(i, j)] = [gyro_data, gtext, [line_gx, line_gy, line_gz]]
                elif i == 2: # temperature
                    temp_data = deque([np.zeros(1)], maxlen=int(maxt/dt))
                    line_t = Line2D([], [], color='red')
                    ax.add_line(line_t)
                    if data_type == 'FM':
                        ax.set_ylim(-40000, 40000)
                    else:
                        ax.set_ylim(-80, 80)
                    ax.set_xlim(0, self.maxt)
                    ttext = ax.text(0.01, 0.85, '', transform=ax.transAxes)
                    ax.legend(['temp'], loc='upper right')
                    self.axs_stats[(i, j)] = [temp_data, ttext, [line_t]]
                elif i == 3: # roll pitch
                    angle_data = deque([np.zeros(2)], maxlen=int(maxt/dt))
                    line_angr = Line2D([], [], color='red')
                    line_angp = Line2D([], [], color='blue')
                    ax.add_line(line_angr)
                    ax.add_line(line_angp)
                    ax.set_ylim(-180, 180)
                    ax.set_xlim(0, self.maxt)
                    angtext = ax.text(0.01, 0.85, '', transform=ax.transAxes)
                    ax.legend(['roll', 'pitch'], loc='upper right')
                    self.axs_stats[(i, j)] = [angle_data, angtext, [line_angr, line_angp]]

    def update(self, data):
        '''
        4xn
        data: np.array{[[[ax1, ay1, az1], [ax2, ay2, az2], ..., [axn, ayn, azn]],
                          [[gx1, gy1, gz1], [gx2, gy2, gz2], ..., [gxn, gyn, gzn]],
                          [[t1],            [t2],            ..., [tn]           ],
                          [[roll1, pitch1], [roll2, pitch2], ..., [rolln, pitchn]]]}
        '''
        myax_status_lst = []
        lastt = self.tdata[-1] + self.dt
        self.tdata.append(lastt)
        for i, axs_row in enumerate(self.axs): # i is row number
            if not isinstance(axs_row, np.ndarray):
                axs_row = np.array([axs_row])
            for j in range(len(axs_row)): # j is column number
                myax = axs_row[j]
                if i == 0 and len(data[i][j]) != 0:
                    ax, ay, az = data[i][j]
                    accel_data = self.axs_stats[(i, j)][0]
                    accel_data.append(np.array([ax, ay, az]))
                    accel_data = np.array(accel_data)
                    atext = self.axs_stats[(i, j)][1]
                    if self.data_type == 'FM':
                        atext.set_text(f"xAccel:{int(ax)} yAccel:{int(ay)} zAccel:{int(az)}")
                    else:
                        atext.set_text(f"xAccel:{'{:<10.3f}'.format(ax)} yAccel:{'{:<10.3f}'.format(ay)} zAccel:{'{:<10.3f}'.format(az)}")
                    line_ax = self.axs_stats[(i, j)][2][0]
                    line_ay = self.axs_stats[(i, j)][2][1]
                    line_az = self.axs_stats[(i, j)][2][2]
                    line_ax.set_data(self.tdata, accel_data[:, 0])
                    line_ay.set_data(self.tdata, accel_data[:, 1])
                    line_az.set_data(self.tdata, accel_data[:, 2])
                    myax_status_lst.append(line_ax)
                    myax_status_lst.append(line_ay)
                    myax_status_lst.append(line_az)
                    myax_status_lst.append(atext)
                elif i == 1 and len(data[i][j]) != 0:
                    gx, gy, gz = data[i][j]
                    gyro_data = self.axs_stats[(i, j)][0]
                    gyro_data.append(np.array([gx, gy, gz]))
                    gyro_data = np.array(gyro_data)
                    gtext = self.axs_stats[(i, j)][1]
                    if self.data_type == 'FM':
                        gtext.set_text(f"xGyro:{int(gx)} yGyro:{int(gy)} zGyro:{int(gz)}")
                    else:
                        gtext.set_text(f"xGyro:{'{:<10.3f}'.format(gx)} yGyro:{'{:<10.3f}'.format(gy)} zGyro:{'{:<10.3f}'.format(gz)}")
                    line_gx = self.axs_stats[(i, j)][2][0]
                    line_gy = self.axs_stats[(i, j)][2][1]
                    line_gz = self.axs_stats[(i, j)][2][2]
                    line_gx.set_data(self.tdata, gyro_data[:, 0])
                    line_gy.set_data(self.tdata, gyro_data[:, 1])
                    line_gz.set_data(self.tdata, gyro_data[:, 2])
                    myax_status_lst.append(line_gx)
                    myax_status_lst.append(line_gy)
                    myax_status_lst.append(line_gz)
                    myax_status_lst.append(gtext)
                elif i == 2 and len(data[i][j]) != 0:
                    t = data[i][j][0]
                    temp_data = self.axs_stats[(i, j)][0]
                    temp_data.append(np.array([t]))
                    temp_data = np.array(temp_data)
                    ttext = self.axs_stats[(i, j)][1]
                    if self.data_type == 'FM':
                        ttext.set_text(f"temp:{int(t)}")
                    else:
                        ttext.set_text(f"temp:{'{:<10.3f}'.format(t)}")
                    line_t = self.axs_stats[(i, j)][2][0]
                    line_t.set_data(self.tdata, temp_data[:, 0])
                    myax_status_lst.append(line_t)
                    myax_status_lst.append(ttext)
                elif i == 3 and len(data[i][j]) != 0:
                    roll, pitch = data[i][j]
                    angle_data = self.axs_stats[(i, j)][0]
                    angle_data.append(np.array([roll, pitch]))
                    angle_data = np.array(angle_data)
                    angtext = self.axs_stats[(i, j)][1]
                    angtext.set_text(f"roll:{'{:<10.3f}'.format(roll)} pitch:{'{:<10.3f}'.format(pitch)}")
                    line_angr = self.axs_stats[(i, j)][2][0]
                    line_angp = self.axs_stats[(i, j)][2][1]
                    line_angr.set_data(self.tdata, angle_data[:, 0])
                    line_angp.set_data(self.tdata, angle_data[:, 1])
                    myax_status_lst.append(line_angr)
                    myax_status_lst.append(line_angp)
                    myax_status_lst.append(angtext)
                myax.set_xlim(self.tdata[0], lastt)
        return myax_status_lst

class Visual:
    def __init__(self, stdscr, data_type, maxt, dt, emitter=None, chip_number=None):
        self.data_type = data_type
        if data_type == 'FM':
            self.fig, axs = plt.subplots(3, chip_number, figsize=(10, 6))
        elif data_type == 'A1' or data_type == 'A2':
            self.fig, axs = plt.subplots(4, 1, figsize=(10, 6))
        else:
            self.fig, axs = plt.subplots(3, 1, figsize=(10, 6))
        self.scope = Scope(axs, maxt, dt, data_type)
    
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
