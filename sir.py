# written by ssh0, September 2014.
# function to move population added by chari8, March  2017.


## Parameters and definitions
from tkinter import *
import numpy as np
import sys
import collections
import math
from enum import Enum
import math
import pdb

## ---------- Parameters ---------------
# Flags
isAgent = True
isTriangle = False
isSIRS = False
settingAreaMode = 0
isSetHotSpot = False
useGradColor = True

# Probability Setting
beta = 0.3 # Rate of Infection
default_i_ratio = 0.001 #0.001 # ration of initial infected

# Time
Tmax = 1000
RecTime = 10
SusTime = 10

# Size
L = 50 #150 #grid number
default_size = 540 #1080  # default size of canvas
default_population = 10000  #default population number
default_cell_size = 20  #default cell size

# File
RANGE = "range_sample/range_tkb3.txt"
LINES = "lines_sample/lines_giza.txt"
OUTPUT = "output.txt"

# HotSpot (感染しやすい点)
hotSpot = []

# For Debug
isDebug = False
## ---------- End ---------------

# Status Text
STATUS = ""


# State Setting
class State(Enum):
    block = 3
    recover = 2
    suscept = 0
    infect = 1


# Color Setting
susCol = "white"
infCol = "red"
recCol = "blue"
blockCol = "grey"
hotCol = "green"


# Enum2Color
enum2color = [susCol, infCol, recCol, blockCol]
#enum2color = [blockCol, recCol, susCol, infCol]
num2State = ["S", "I", "R", "Block"]


# Useful functions
def isEven(x):
    return x%2 == 0

def isDelta(x,y):
    return isEven(x+y)

def isNabla(x,y):
    return not isDelta(x,y)


# Color func

def sigmoid(x, gain=1, offset_x=0):
    return ((np.tanh(((x + offset_x)*gain)/2)+1)/2)

def sigColor(x):
    global useGradColor
    rgbnum = 255
    if useGradColor:
        red = 1
        green = 1-x
        blue = 1-x
    else:
        gain = 10
        offset_red = -0.1
        offset_blue = -1*offset_red
        offset_green = 0.3
        x = (x * 2 ) -1
        red = sigmoid(x, gain, offset_red*2)
        blue = 1 - sigmoid(x, gain, offset_blue*2)
        green = sigmoid(x, gain, offset_green*2) + (1-sigmoid(x, gain, -1*offset_green*2))
        green = green -1.0
    return "#%02x%02x%02x" % (math.ceil(red*rgbnum), math.ceil(green*rgbnum), math.ceil(blue*rgbnum)) 


# SIRmodel
class SIRmodel:

    def __init__(self, L=30, i_ratio=None, pattern=None):
        self.L = L  # lattice size
        #self.illTime = np.zeros([self.L + 2, self.L + 2, default_cell_size])

        # 範囲設定
        global settingAreaMode
        self.lst = []
        if settingAreaMode > 0:
            #usually not used
            try:
                # Setting Area
                file = RANGE if settingAreaMode==1 else LINES
                for line in open(file, "r"):
                    lsp = line.strip().split("\t")
                    tmps = []
                    while len(lsp) > 0:
                        a = int(lsp.pop(0))
                        b = int(lsp.pop(0))
                        tmps.append([a,b])
                    self.lst.append(tmps)
            except FileNotFoundError:
                print("Error : ", file,"is not found!!!")
                settingAreaMode = 0

        self.lattice = np.zeros([self.L + 2, self.L + 2, default_cell_size*2],dtype=int)

        self.population = np.zeros([default_population, 3],dtype=int) #array for store population
        self.population[:,0] = -1

        self.past_count_dict = []

        """
        if p > 0:
            # 初期感染点の設置
            lattice = np.random.random([self.L + 2, self.L + 2, 10])
            for i in range(L+2):
                for j in range(L+2):
                    if not self.isRange(i,j) :
                        continue                    
                    if lattice[i,j] < p:
                        self.lattice[i,j] = State.infect.value
                    else:
                        self.lattice[i,j] = State.suscept.value
            self.lattice[0, :] = self.lattice[self.L+1, :] = State.suscept.value
            self.lattice[:, 0] = self.lattice[:, self.L + 1] = State.suscept.value
        """

        if i_ratio > 0:
            #set population
            population_address = 0
            self.lattice[:] = -1
            for i in range(1,L+1):
                for j in range(1,L+1):
                    self.lattice[i,j,:4] = 2 #set direction
                    #set people
                    if isAgent:
                        population_num = default_cell_size*2
                    else:
                        population_num = 1  
                    while population_num > default_cell_size:
                        population_num = np.random.poisson(np.round(default_population/(L**2)))
                    for k in range(population_num):
                        if population_address >= default_population:
                            continue
                        self.lattice[i,j,4+k] = population_address
                        if np.random.random() < i_ratio:
                            self.population[population_address,0] = State.infect.value
                        else:
                            self.population[population_address,0] = State.suscept.value
                        population_address += 1
        else:
            if pattern:
                for x, y in pattern:
                    self.lattice[x, y] = State.infect.value

        self.past_lattices = []
        self.t = 0

        # settingAreaMode1 : 範囲外の視覚化
        self.isArea = np.zeros([self.L+2, self.L+2])
        for m in range(1, self.L + 1):
            for n in range(1, self.L + 1):
                self.isArea[m,n] = self.isRange(m,n)
                if not self.isArea[m,n]:
                    self.lattice[m,n,:4] = State.block.value

        # settingAreaMode3 : LINESの設置
        if settingAreaMode == 2:
            self.drawLine(self.lst)

        # HotSpot : Distanceの計算
        self.Rmax = 10
        Rmax = self.Rmax
        self.dist = np.zeros([Rmax, Rmax])
        for i in range(Rmax):
            for j in range(Rmax):
                 if self.dist[j,i] > 0:
                    self.dist[i,j] = self.dist[j,i]
                    self.dist[i,j] = np.sqrt(i**2 + j**2)

    def drawLine(self, dots):
        """only virtical, horizontal or 45degreed lines are allowed"""
        for dt in dots:
            for i in range(len(dt)-1):
                x1,y1 = dt[i]
                x2,y2 = dt[i+1]
                if x1 == x2:
                    head = min(y1,y2+1)
                    tail = max(y1,y2+1)
                    self.lattice[x1, head:tail] = State.block.value
                    self.lattice[x1+1, head:tail] = State.block.value
                elif y1 == y2:
                    head = min(x1,x2+1)
                    tail = max(x1,x2+1)
                    self.lattice[head:tail, y1] = State.block.value
                elif abs(x1-x2) == abs(y1-y2):
                    xb = 1 if x1 <= x2 else -1
                    yb = 1 if y1 <= y2 else -1
                    for i, j in zip(range(x1, x2, xb), range(y1, y2, yb)):
                        self.lattice[i,j] = State.block.value
                else:
                    pass

    def progress(self, canvas_update, canvas_displayStatus, update):
        
        self.loop = True

        while self.loop:
            try:
                past_lattice = self.lattice.copy()
                self.lattice[:, :, 4:] = -1
                self.past_lattices.append(past_lattice)

                # 隣接格子点の判定
                for m in range(1, self.L + 1):
                    for n in range(1, self.L + 1):

                        # 範囲外ならばスキップ
                        if not self.isArea[m,n]:
                            continue

                        # infection processing
                        cell = past_lattice[m,n,4:]
                        totalNum = 0
                        infNum = 0
                        infCell = []
                        susCell = []
                        recCell = []

                        for popAddr in cell:
                            if popAddr == -1 or self.population[popAddr, 0] == -1:
                                continue
                            totalNum += 1
                            state_val =  self.population[popAddr, 0]
                            if state_val == State.suscept.value:
                                susCell.append(popAddr)
                            elif state_val == State.infect.value:
                                infCell.append(popAddr)
                                infNum += 1
                            else:
                                recCell.append(popAddr)

                        if not isAgent:
                            if self.population[past_lattice[m-1,n,4],0] == State.infect.value:
                                infNum += 1
                            if self.population[past_lattice[m+1,n,4],0] == State.infect.value:
                                infNum += 1
                            if not(isTriangle and isNabla(m,n)): 
                                if self.population[past_lattice[m,n-1,4],0] == State.infect.value:
                                    infNum += 1
                            if not(isTriangle and isDelta(m,n)):
                                if self.population[past_lattice[m,n+1,4],0] == State.infect.value:
                                    infNum += 1
                            

                        #q = np.exp(beta * infNum / totalNum)
                        q = 1 - (1-self.getBeta(m,n))**infNum

                        for susPopAddr in susCell:
                            if np.random.random() <= q:
                                self.population[susPopAddr, 0] = State.infect.value

                        for infPopAddr in infCell:
                            if self.population[infPopAddr, 1] > RecTime:
                                self.population[infPopAddr, 0] = State.recover.value
                                if not isSIRS:
                                    self.population[infPopAddr, 1] = 0
                            else:
                                self.population[infPopAddr, 1] += 1

                        for recPopAddr in recCell:
                            if isSIRS:
                                if self.population[recPopAddr, 1] > RecTime + SusTime:
                                    self.population[recPopAddr, 0] = State.suscept.value
                                    self.population[recPopAddr, 1] = 0
                                else:
                                    self.population[recPopAddr, 1] += 1

                        #move people
                        tri = np.tri(4, dtype=int).transpose()
                        direction = np.dot(past_lattice[m,n, :4], tri).astype(np.float64) / 10
                        for popAddr in cell:
                            if popAddr == -1 or self.population[popAddr, 0] == -1:
                                continue
                            if isAgent:
                                direction_num = np.where(direction < np.random.random())[0].shape[0]
                                if direction_num == 0 and (past_lattice[m-1, n, :4] == -1).all(): #is upper cell is in range?
                                    direction_num = 1
                                if direction_num == 1 and (past_lattice[m+1, n, :4] == -1).all(): #is lower cell is in range?
                                    direction_num = 0
                                if direction_num == 2 and (past_lattice[m, n-1, :4] == -1).all(): #is left cell is in range?
                                    direction_num = 3
                                if direction_num == 3 and (past_lattice[m, n+1, :4] == -1).all(): #is right cell is in range?
                                    direction_num = 2
                            else:
                                direction_num = 4 #stay in the same cell    

                            if direction_num == 0: #go up
                                position = np.where(self.lattice[m-1, n, 4:] == -1)[0]
                                self.lattice[m-1, n, 4+position[0]] = popAddr
                            elif direction_num == 1: #go down
                                position = np.where(self.lattice[m+1, n, 4:] == -1)[0]
                                self.lattice[m+1, n, 4+position[0]] = popAddr
                            elif direction_num == 2: # go left
                                position = np.where(self.lattice[m, n-1, 4:] == -1)[0]
                                self.lattice[m, n-1, 4+position[0]] = popAddr
                            elif direction_num == 3: # go right
                                position = np.where(self.lattice[m, n+1, 4:] == -1)[0]
                                self.lattice[m, n+1, 4+position[0]] = popAddr
                            else: #stay in the same cell
                                position = np.where(self.lattice[m, n, 4:] == -1)[0]
                                self.lattice[m, n, 4+position[0]] = popAddr

                        """
                        if past_lattice[m,n] == State.suscept.value:
                            ## 感染判定
                            
                            # 周囲のinfect.value数を調べる
                            neighber = 0
                            if past_lattice[m-1,n] == State.infect.value:
                                neighber += 1
                            if past_lattice[m+1,n] == State.infect.value:
                                neighber += 1
                            if not(isTriangle and isNabla(m,n)): 
                                if past_lattice[m,n-1] == State.infect.value:
                                    neighber += 1
                            if not(isTriangle and isDelta(m,n)):
                                if past_lattice[m,n+1] == State.infect.value:
                                    neighber += 1
                            # 各感染者から感染するか計算
                            for i in range(neighber):
                                if np.random.random() < self.getBeta(m,n):
                                    self.lattice[m,n] = State.infect.value
                        elif self.lattice[m,n] == State.infect.value:
                            # State = InfectならばillTimeをインクリメント
                            # 一定時間でInfectからRecoverへ
                            if self.illTime[m,n] > RecTime:
                                self.lattice[m,n] = State.recover.value
                            else:
                                self.illTime[m,n] += 1
                        elif self.lattice[m,n] == State.recover.value:
                            # SIRSModelならばSusceptへ変化
                            if isSIRS:
                                if self.illTime[m,n] > RecTime + SusTime:
                                    self.illTime[m,n] = 0
                                    self.lattice[m,n] = State.suscept.value
                                else:
                                    self.illTime[m,n] += 1
                        else:
                            continue
                        """

                # 描画の更新
                changed_rect = np.where(self.lattice != past_lattice)
                for x, y in zip(changed_rect[0], changed_rect[1]):
                    if [x,y] not in hotSpot:
                        #color = enum2color[self.lattice[x,y]]
                        #color = sigColor(self.lattice[x,y]/4)
                        cell = self.lattice[x,y, 4:]
                        totalNum = 0
                        infNum = 0
                        susNum = 0
                        for popAddr in cell:
                            if popAddr == -1 or self.population[popAddr, 0] == -1:
                                continue
                            totalNum += 1
                            state_val = self.population[popAddr, 0]
                            if state_val == State.infect.value:
                                infNum += 1
                            elif state_val == State.infect.value:
                                susNum += 1
                        if totalNum == 0:
                            param = 0
                        else:
                            param = infNum / totalNum
                        color = sigColor(param)
                        canvas_update(x, y, color)
                update()
                # time.sleep(0.1)

                # 状態更新
                self.t += 1
                if self.t > Tmax:
                    self.loop = False

                # 状態表示
                canvas_displayStatus(self.lattice, self.population, self.past_count_dict)

            except KeyboardInterrupt:
                print("stopped.")
                break

    def isRange(self, x, y):

        if settingAreaMode != 1:
            return True
        head = 0 #self.L // 6
        yd = y - head
        if yd < 0 or yd > len(self.lst)-1:
            return False
        for ls in self.lst[yd]:
            minX, maxX = ls
            if x > minX and x < maxX:
                return True
        return False

    def getBeta(self, x, y):

        Rmax = self.Rmax
        for X,Y in hotSpot:
            disX = abs(X - x)
            disY = abs(Y - y)
            if (disX < Rmax) and (disY < Rmax):
                if X == x and Y == y:
                    return 1.0 #コアは絶対感染
                d = self.dist[disX, disY]
                if d > 0:
                    return min(beta * (1 + 10/d),1.0)
        return beta

    def rewind(self, canvas_update, canvas_displayStatus, update):
        """not available currently"""

        self.loop = True
        future_lattice = self.lattice
        while self.loop:

            tmp_lattice = self.past_lattices.pop()
            changed_rect = np.where(tmp_lattice != future_lattice)
            for x, y in zip(changed_rect[0], changed_rect[1]):
                color = enum2color[tmp_lattice[x, y]]
                #color = sigColor(tmp_lattice[x,y]/4)
                canvas_update(x, y, color)
                self.lattice = tmp_lattice
                if self.lattice[x,y] == State.infect.value:
                   self.illTime[x,y] -= 1
            update()

            self.t -= 1
            if len(self.past_lattices) == 0:
                self.loop = False
                canvas_displayStatus(tmp_lattice)

class Draw_canvas:
    """class to Draw_canvas"""

    def __init__(self, lg, L):
        self.lg = lg
        self.L = L
        self.r = int(default_size / (2 * self.L))
        self.fig_size = 2 * self.r * self.L
        self.margin = 10
        self.sub = Toplevel()
        self.sub.title("SIR Model")
        self.canvas = Canvas(self.sub, width=self.fig_size + 2 * self.margin,
                             height=self.fig_size + 10 * self.margin)
        self.cr = self.canvas.create_rectangle
        self.ct = self.canvas.create_polygon
        self.update = self.canvas.update
        self.rects = dict()
        self.past_count_dict = []

        #under dev
        for x in range(1, self.L + 1):
            for y in range(1, self.L + 1):
                """here goes function to show specific params of lattice default:infection ratio"""
                cell = self.lg.lattice[x,y,4:]
                totalNum = 0
                infNum = 0
                susNum = 0
                for popAddr in cell:
                    if popAddr == -1 or self.lg.population[popAddr,0] == -1:
                        continue
                    totalNum += 1
                    state_val = self.lg.population[popAddr,0]
                    if state_val == State.infect.value:
                        infNum += 1
                    elif state_val == State.infect.value:
                        susNum += 1
                if totalNum == 0:
                    param = 0
                else:
                    param = infNum / totalNum
                tag = "%d %d" % (x, y)
                self.rects[tag] = Poly(x, y, param, tag, self)
                
        self.canvas.pack(side=LEFT, expand=YES, fill=BOTH)

        #for st in num2State:
            #print(st,":\t", end="")

        buf = "Total\tSuscept\tInfect\tRecover\n"
        print(buf, end="")

        if not isDebug:
            with open(OUTPUT, 'a') as f:
                f.write(buf)
                f.close()
        
    def canvas_update(self, x, y, color):
        try:
            v = self.rects["%d %d" % (x, y)]
            v.root.canvas.itemconfig(v.ID, fill=color)
        except:
            pass
        
    def canvas_displayStatus(self, lat, population, past_count_dict):
        
        totalNum = np.where(population[:, 0] != -1)[0].shape[0]
        totalSusNum = np.where(population[:, 0] == State.suscept.value)[0].shape[0]
        totalInfNum = np.where(population[:, 0] == State.infect.value)[0].shape[0]
        totalRecNum = np.where(population[:, 0] == State.recover.value)[0].shape[0]

        count_dict = [totalNum, totalSusNum, totalInfNum, totalRecNum]
        past_count_dict.append(count_dict)

        buf = ""
        for nums in count_dict:
            bf = str(nums) + "\t"
            buf += bf
        buf += "\n"
            
        if not isDebug:
            print(buf, end="")
            with open(OUTPUT, 'a') as f:
                f.write(buf)
                f.close()

        """
        tmp = []
        for i in range(1,self.L+1):
            for j in range(1,self.L+1):
                tmp.append(lat[i,j])
        count_dict = []
        for k, s in enumerate(num2State):
            count_dict.append([s, tmp.count(k)])
            
        # # 最後の項にはTotalを記載
        # count_dict[3][1] = self.L**2 - count_dict[3][1]

        if count_dict != self.past_count_dict:
            buf = ""
            for k,v in count_dict:
                bf = str(v) + '\t'
                buf += bf
            buf += '\n'

            if not isDebug:
                print(buf, end="")
                with open(OUTPUT, 'a') as f:
                    f.write(buf)
                    f.close()

        self.past_count_dict = count_dict
        """

class Poly:
    """export each polygon with sigcolor"""

    def __init__(self, x, y, param, tag, root):
        self.root = root
        self.x = x
        self.y = y
        #self.live = live
        #color = enum2color[live]
        #color = sigColor(live/4)
        color = sigColor(param)
        size = 2 #2.5
        triangles = [[0, 0, 0.5, -1, 1, 0], [0, -1, 0.5, 0, 1, -1]] #Δ、∇
        xh = x/2
        isD = isDelta(x,y)
        outline_color = "grey"
        wid = 0.1

        if isTriangle:
            self.ID = self.root.ct(size*(xh + triangles[isD][0])*self.root.r + self.root.margin,
                               size*(y + triangles[isD][1])*self.root.r + self.root.margin,
                              size*(xh + triangles[isD][2])*self.root.r + self.root.margin,
                              size*(y + triangles[isD][3])*self.root.r + self.root.margin,
                               size*(xh + triangles[isD][4])*self.root.r + self.root.margin,
                              size*(y + triangles[isD][5])*self.root.r + self.root.margin,
                                outline=outline_color, fill=color, tag=tag, width=wid)
        else:
            self.ID = self.root.cr(size*(x-1)*self.root.r + self.root.margin,
                              size*(y-1)*self.root.r + self.root.margin,
                              size*x*self.root.r + self.root.margin,
                              size*y*self.root.r + self.root.margin,
                              outline=outline_color, fill=color, tag=tag, width=wid)
        #self.root.canvas.tag_bind(self.ID, '<Button-1>', self.showNum) #left click
        #self.root.canvas.tag_bind(self.ID, '<Button-2>', self.showNum) #right click

    def showNum(self, event):
        pass

    """
    def pressedL(self, event):
        x,y = self.x, self.y

        if isSetHotSpot:

            # toggle
            if [x,y] not in hotSpot:
                hotSpot.append([x,y])
                color = hotCol
            else:
                hotSpot.remove([x,y])
                color = susCol
        else:
            # toggle
            if self.live == State.suscept.value:
                color = infCol
                self.root.lg.lattice[x, y] = State.infect.value
                self.live = State.infect.value
            elif self.live == State.infect.value:
                color = susCol
                self.root.lg.lattice[x, y] = State.suscept.value
                self.live = State.suscept.value
            else:
                color = enum2color[self.live]
        self.root.canvas.itemconfig(self.ID, fill=color)

    def pressedR(self, event):
        # toggle        
        if self.live == State.suscept.value:
            color = blockCol
            self.live = State.block.value
            self.root.lg.lattice[self.x, self.y] = State.block.value
        else:
            color = susCol
            self.live = State.suscept.value
            self.root.lg.lattice[self.x, self.y] = State.suscept.value
        self.root.canvas.itemconfig(self.ID, fill=color)
    """


class TopWindow:

    def __init__(self):
        self.root = Tk()

    def show_window(self, title="title", *args):
        self.root.title(title)
        frames = []

        # Frame Button
        for i, arg in enumerate(args):
            frames.append(Frame(self.root, padx=5, pady=5))
            for k, v in arg:
                Button(frames[i], text=k, command=v).pack(expand=YES, fill='x')
            frames[i].pack(fill='x')

        # Config
        Label(text = 'Config').pack(anchor = W)

        # Grid(Radiobutton)
        self.tmp_grid = BooleanVar()
        Label(text = 'Grid:').pack()
        triButton = Radiobutton(self.root, text="△", value=True, variable=self.tmp_grid, command=self.changeGrid)
        squButton = Radiobutton(self.root, text="□", value=False, variable=self.tmp_grid, command=self.changeGrid)
        if isTriangle:
            triButton.select()
        else:
            squButton.select()
        triButton.pack(anchor=W)
        squButton.pack(anchor=W)

        # Model(Radiobutton)
        self.tmp_model = BooleanVar()
        Label(text = 'Model:').pack()
        SIRButton = Radiobutton(self.root, text="SIR", value=False, variable=self.tmp_model, command=self.changeModel)
        SIRSButton = Radiobutton(self.root, text="SIRS", value=True, variable=self.tmp_model, command=self.changeModel)
        if isSIRS:
            SIRSButton.select()
        else:
            SIRButton.select()
        SIRButton.pack(anchor = W)
        SIRSButton.pack(anchor = W)

        # Agent(Radiobutton)
        self.tmp_agent = BooleanVar()
        Label(text = 'Population :').pack()
        FixButton = Radiobutton(self.root, text="Fix", value=False, variable=self.tmp_agent, command=self.changeisAgent)
        UnfixButton = Radiobutton(self.root, text="Unfix", value=True, variable=self.tmp_agent, command=self.changeisAgent)
        if isAgent:
            UnfixButton.select()
        else:
            FixButton.select()
        FixButton.pack(anchor = W)
        UnfixButton.pack(anchor = W)

        # Probability(Scale)
        self.tmp_prob = DoubleVar()
        Label(text = 'Beta(%):').pack()
        scale = Scale(self.root, from_=0, to=100, orient=HORIZONTAL, variable=self.tmp_prob, command=self.changeBeta)
        scale.set(beta * 100)
        scale.pack()

        # Recover time(Entry)
        self.tmp_rectime = StringVar()
        Label(text = 'Recover Time:').pack()
        EboxR = Entry(self.root, textvariable=self.tmp_rectime)
        EboxR.insert(END, RecTime)
        EboxR.pack()
        EboxR.bind('<Return>', self.changeRectime)

        # Suscept time(Entry)
        self.tmp_sustime = StringVar()
        Label(text = 'Restoration Time:').pack()
        EboxS = Entry(self.root, textvariable=self.tmp_sustime)
        EboxS.insert(END, SusTime)
        EboxS.pack()
        EboxS.bind('<Return>', self.changeSustime)

        # Range or Lines(RadioButton and Entry)
        self.tmp_mode = IntVar()
        self.tmp_state = 'disabled'
        Label(text = 'Infection Area Mode:').pack()
        ModeButtonNo = Radiobutton(self.root, text="No limit", value=0, variable=self.tmp_mode, command=self.changeMode)
        ModeButtonRange = Radiobutton(self.root, text="Range", value=1, variable=self.tmp_mode, command=self.changeMode)
        ModeButtonLines = Radiobutton(self.root, text="Lines", value=2, variable=self.tmp_mode, command=self.changeMode)
        ModeButtonNo.select()
        ModeButtonNo.pack(anchor = W)
        ModeButtonRange.pack(anchor = W)
        ModeButtonLines.pack(anchor = W)

        self.tmp_file = StringVar()
        Label(text = 'File Name:').pack()
        EboxRange = Entry(self.root, textvariable=self.tmp_file, state=self.tmp_state)
        EboxRange.pack()
        EboxRange.bind('<Return>', self.changeRange)
        self.EboxRange = EboxRange

        # SwitchLeftButton(Radiobutton)
        self.tmp_hotspot = IntVar()
        Label(text = 'LeftButton :').pack()
        InfectedButton = Radiobutton(self.root, text="Infected", value=False, variable=self.tmp_hotspot, command=self.setHotSpot)
        HotSpotButton = Radiobutton(self.root, text="HotSpot", value=True, variable=self.tmp_hotspot, command=self.setHotSpot)
        InfectedButton.select()
        InfectedButton.pack(anchor = W, side=LEFT)
        HotSpotButton.pack(anchor = W, side=RIGHT)

        self.root.mainloop()

    def changeGrid(self):
        global isTriangle
        isTriangle = self.tmp_grid.get()

    def changeModel(self):
        global isSIRS
        isSIRS = self.tmp_model.get()

    def changeisAgent(self):
        global isAgent
        isAgent = self.tmp_agent.get()

    def changeBeta(self, b):
        global beta
        beta = float(b)/100.0

    def changeRectime(self, event):
        global RecTime
        RecTime = int(self.tmp_rectime.get())

    def changeSustime(self, event):
        global SusTime
        SusTime = int(self.tmp_sustime.get())

    def changeMode(self):
        global settingAreaMode
        settingAreaMode = self.tmp_mode.get()
        self.tmp_state = 'normal' if settingAreaMode > 0 else 'disabled'
        self.EboxRange.configure(state=self.tmp_state)
        self.EboxRange.delete(0, END)
        if settingAreaMode > 0:
            file = RANGE if settingAreaMode==1 else LINES
            self.EboxRange.insert(END, file)            
            
    def changeRange(self, event):
        if settingAreaMode == 1:
            global RANGE
            RANGE = self.tmp_file.get()
        else:
            global LINES
            LINES = self.tmp_file.get()

    def setHotSpot(self):
        global isSetHotSpot        
        isSetHotSpot = self.tmp_hotspot.get()

class Main:
    
    def __init__(self):
        self.top = TopWindow()
        self.top.show_window("SIR Model",
                             (('clear set', self.clearSet),
                             ('random set', self.randSet),
                             ),
                             (('▶', self.start),
                              ('□', self.pause),
                              ('◁◁', self.rewind),
                             ),
                             (('save', self.pr),),
                             (('quit', self.quit),))

    def clearSet(self):
        if 'self.lg.loop' in locals():
            self.pause()
        self.lg = SIRmodel(L, i_ratio=0, pattern=None)
        self.DrawCanvas = Draw_canvas(self.lg, self.lg.L)

    def randSet(self):
        if 'self.lg.loop' in locals():
            self.pause()
        self.lg = SIRmodel(L, i_ratio=default_i_ratio, pattern=None)
        self.DrawCanvas = Draw_canvas(self.lg, self.lg.L)

    def start(self):
        self.lg.progress(self.DrawCanvas.canvas_update, self.DrawCanvas.canvas_displayStatus, self.DrawCanvas.update)

    def rewind(self):
        self.lg.rewind(self.DrawCanvas.canvas_update, self.DrawCanvas.canvas_displayStatus, self.DrawCanvas.update)

    def pause(self):
        self.lg.loop = False

    def pr(self):
        import tkinter.filedialog
        import os
        if self.DrawCanvas is None:
            return 1
        fTyp = [('eps file', '*eps'), ('all files', '*')]
        filename = tkinter.filedialog.asksaveasfilename(filetypes=fTyp,
                                                  initialdir=os.getcwd(),
                                                  initialfile='figure_1.eps')
        if filename is None:
            return 0
        self.DrawCanvas.canvas.postscript(file=filename)

    def quit(self):
        if 'self.lg.loop' in locals():
            self.pause()
        sys.exit()

if __name__ == '__main__':
    app = Main()
