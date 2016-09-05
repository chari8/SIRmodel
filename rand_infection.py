import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import matplotlib.animation as animation
import random as rd
import math
from enum import Enum
import time as tm

class State(Enum):
    SUS = 0
    INF = 1
    REC = 2
    
def getVec():
    norm = 1
    rx = rd.random() * (-1)**rd.randint(0,1)
    ry = math.sqrt(1 - rx * rx) * (-1)**rd.randint(0,1)
    return [norm*rx, norm*ry]

def isNearInf(ax, ay, bx, by, R):
    if abs(ax - bx) < R and abs(bx - by) < R:
        return (ax - bx)**2 + (ay - by)**2 < R**2
    return False

class Point:
    def __init__(self, x, y, dx, dy, state, period):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.state = state
        self.period = period
        
## Parameter
rangeMax = 100
numPoint = 1000
beta = 0.1
time = 200
recover_time = time/2
div_time = time / 20
R = 5
subR = 20

fig = plt.figure()
points = []
ims = []

st = tm.time()
#Init
for i in range(numPoint):
    ## Init Position
    x = rangeMax * rd.random()
    y = rangeMax * rd.random()
            
    ## Random Move
    dx, dy = getVec()

    ## Init Infected Person
    if i == 0:
        state = State.INF
    else:
        state = State.SUS
    period = 0
    p = Point(x, y, dx, dy, state, period)
    points.append(p)

for t in range(time):
    ## Init
    sus_x = []
    sus_y = []
    inf_x = []
    inf_y = []
    rec_x = []
    rec_y = []

    for pt in points:

        ## Refrection
        if pt.x + pt.dx < 0 or pt.x + pt.dx > rangeMax:
            pt.dx = -pt.dx
        if pt.y + pt.dy < 0 or pt.y + pt.dy > rangeMax:
            pt.dy = -pt.dy

        ## Move
        pt.x += pt.dx
        pt.y += pt.dy

        ## Extract        
        if  pt.state == State.SUS:
            sus_x.append(pt.x)
            sus_y.append(pt.y)
        elif pt.state == State.INF:
            inf_x.append(pt.x)
            inf_y.append(pt.y)
        else:
            rec_x.append(pt.x)
            rec_y.append(pt.y)
            
    im = plt.plot(sus_x, sus_y, "ob", inf_x, inf_y, "or", rec_x, rec_y, "og")
    ims.append(im)

    ## Infection Phase        
    for pt in points:
        if pt.state == State.SUS:
            for i in range(len(inf_x)):
                if isNearInf(inf_x[i], inf_y[i], pt.x, pt.y, R):
                    if rd.random() < beta:
                        pt.state = State.INF
                
    ## Recover Phase
    for pt in points:
        if pt.state == State.INF:
            if pt.period > recover_time:
                pt.state = State.REC
                pt.period = 0
            else:
                pt.period += 1                
            # print(pt.period)            
            
print(tm.time()-st)

# 動画保存の準備
Writer = animation.writers['ffmpeg']
writer = Writer(fps=15, metadata=dict(artist='Me'), bitrate=1800)

ani = animation.ArtistAnimation(fig, ims, interval=50, repeat_delay=1000)

#動画として保存
plt.show()
#ani.save("sirs_model.mp4", writer=writer)
