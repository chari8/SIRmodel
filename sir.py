#! /usr/bin/env python
# -*- coding:utf-8 -*-
#
# written by ssh0, September 2014.

from tkinter import *
import numpy as np
import sys
import collections
import math
from enum import Enum

# import time

## ---------- Parameters ---------------
# Rec or Tri Mode
isTriangle = True
isSIRS = False
SettingArea = False
isSetHotSpot = False

# Probability Setting
beta = 0.3 # Rate of Infection
prob = 0.001 # Primitive infection probability

# Time
Tmax = 1000
RecTime = 10
SusTime = 10

# Size
L = 100
default_size = 1080  # default size of canvas

# File
RANGE = "range_sample/range_ko.txt"
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
    suscept = 0
    infect = 1
    recover = 2
    block = 3

# Color Setting
susCol = "white"
infCol = "red"
recCol = "blue"
blockCol = "grey"
hotCol = "green"

# Enum2Color
enum2color = [susCol, infCol, recCol, blockCol]
num2State = ["S", "I", "R", "Total"]

# Useful functions
def isEven(x):
    return x%2 == 0

def isDelta(x,y):
    return isEven(x+y)

def isNabla(x,y):
    return not isDelta(x,y)

class SIRmodel:

    def __init__(self, L=30, p=None, pattern=None):
        self.L = L  # lattice size
        self.illTime = np.zeros([self.L + 2, self.L + 2])

        # 範囲設定
        global SettingArea
        self.lst = []
        try:
            # Setting Area
            if SettingArea:
                for line in open(RANGE, "r"):
                    lsp = line.strip().split("\t")
                    tmps = []
                    while len(lsp) > 0:
                        tmp = [0,0]
                        tmp[0] = int(lsp.pop(0))
                        tmp[1] = int(lsp.pop(0))
                        tmps.append(tmp)
                    self.lst.append(tmps)
        except FileNotFoundError:
            print("Error : ", RANGE,"is not found!!!")
            SettingArea = False

        if p > 0:
            lattice = np.random.random([self.L + 2, self.L + 2])
            self.lattice = np.zeros([self.L + 2, self.L + 2], dtype=int) 
            for i in range(L+2):
                for j in range(L+2):
                    if not self.isRange(i,j):
                        continue
                    
                    if lattice[i,j] < p:
                        self.lattice[i,j] = State.infect.value
                    else:
                        self.lattice[i,j] = State.suscept.value
            self.lattice[0, :] = self.lattice[self.L+1, :] = State.suscept.value
            self.lattice[:, 0] = self.lattice[:, self.L + 1] = State.suscept.value
        else:
            self.lattice = np.zeros([self.L + 2, self.L + 2], dtype=int)
            if pattern:
                for x, y in pattern:
                    self.lattice[x, y] = State.infect.value
        self.past_lattices = []
        self.t = 0

        # 範囲外の視覚化
        self.isArea = np.zeros([self.L+2, self.L+2])
        for m in range(1, self.L + 1):
            for n in range(1, self.L + 1):
                self.isArea[m,n] = self.isRange(m,n)
                if not self.isArea[m,n]:
                    self.lattice[m,n] = State.block.value

        # 感染確率点準備
        # div = 3
        # self.points = []
        # for i in range(div):
        #     for j in range(div):
        #         self.lattice[i * self.L//div, j * self.L//div] = State.block.value
        #         self.points.append([i * self.L//div, j * self.L//div])
        
        self.Rmax = 10
        Rmax = self.Rmax
        self.dist = np.zeros([Rmax, Rmax])
        for i in range(Rmax):
            for j in range(Rmax):
                if self.dist[j,i] > 0:
                    self.dist[i,j] = self.dist[j,i]
                self.dist[i,j] = np.sqrt(i**2 + j**2)

    def progress(self, canvas_update, canvas_displayStatus, update):
        
        self.loop = True

        while self.loop:
            try:                
                past_lattice = self.lattice.copy()
                self.past_lattices.append(past_lattice)

                # 隣接格子点の判定
                for m in range(1, self.L + 1):
                    for n in range(1, self.L + 1):

                        # 範囲外ならばスキップ
                        if not self.isArea[m,n]:
                            continue
                        
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
                
                # 描画の更新
                changed_rect = np.where(self.lattice != past_lattice)
                for x, y in zip(changed_rect[0], changed_rect[1]):
                    if [x,y] not in hotSpot:
                        color = enum2color[self.lattice[x,y]]
                        canvas_update(x, y, color)
                update()
                # time.sleep(0.1)

                # 状態更新
                self.t += 1
                if self.t > Tmax:
                    self.loop = False

                # 状態表示
                canvas_displayStatus(self.lattice)

            except KeyboardInterrupt:
                print("stopped.")
                break

    def isRange(self, x, y):

        if not SettingArea:
            return True
        head = self.L // 6
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
        
        self.loop = True
        future_lattice = self.lattice
        while self.loop:
            
            tmp_lattice = self.past_lattices.pop()
            changed_rect = np.where(tmp_lattice != future_lattice)
            for x, y in zip(changed_rect[0], changed_rect[1]):
                color = enum2color[tmp_lattice[x, y]]
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

        # 画像の挿入は廃止
        # Image
        # self.img = PhotoImage(file=TKB)
        # lab = Label(self.canvas, image=self.img)
        # lab.place(x=0, y=0, relwidth=1, relheight=1)
        # self.canvas.tag_lower(lab)
        # playButton = Button(self.canvas, text='Play')
        # playButton.pack()        
                     
        for x in range(1, self.L + 1):
            for y in range(1, self.L + 1):
                live = self.lg.lattice[x,y]
                tag = "%d %d" % (x, y)
                self.rects[tag] = Poly(x, y, live, tag, self)

        self.canvas.pack()                        
    
    def canvas_update(self, x, y, color):
        try:
            v = self.rects["%d %d" % (x, y)]
            v.root.canvas.itemconfig(v.ID, fill=color)
        except:
            pass
        
    def canvas_displayStatus(self, lat):
        
        tmp = []
        for i in range(1,self.L+1):
            for j in range(1,self.L+1):
                tmp.append(lat[i,j])
        count_dict = []
        for k, s in enumerate(num2State):
            count_dict.append([s, tmp.count(k)])
            
        # 最後の項にはTotalを記載
        count_dict[3][1] = self.L**2 - count_dict[3][1]
        
        if count_dict != self.past_count_dict:            
            buf = ""
            for k,v in count_dict:
                bf = k + ':' + str(v) + '\t'
                buf += bf
            buf += '\n'

            if not isDebug:
                print(buf, end="")            
                with open(OUTPUT, 'a') as f:
                    f.write(buf)
                    f.close()
            
        self.past_count_dict = count_dict

class Poly:

    def __init__(self, x, y, live, tag, root):
        self.root = root
        self.x = x
        self.y = y
        self.live = live
        color = enum2color[live]
        size = 1.5
        triangles = [[0, 0, 0.5, -1, 1, 0], [0, -1, 0.5, 0, 1, -1]] #Δ、∇
        xh = x/2
        isD = isDelta(x,y)
        outline_color = "#030303"

        if isTriangle:
            self.ID = self.root.ct(size*(xh + triangles[isD][0])*self.root.r + self.root.margin,
                               size*(y + triangles[isD][1])*self.root.r + self.root.margin,
                              size*(xh + triangles[isD][2])*self.root.r + self.root.margin,
                              size*(y + triangles[isD][3])*self.root.r + self.root.margin,
                               size*(xh + triangles[isD][4])*self.root.r + self.root.margin,
                              size*(y + triangles[isD][5])*self.root.r + self.root.margin,
                              outline=outline_color, fill=color, tag=tag)
        else:
            self.ID = self.root.cr(size*(x-1)*self.root.r + self.root.margin,
                              size*(y-1)*self.root.r + self.root.margin,
                              size*x*self.root.r + self.root.margin,
                              size*y*self.root.r + self.root.margin,
                              outline=outline_color, fill=color, tag=tag)
        self.root.canvas.tag_bind(self.ID, '<Button-1>', self.pressedL)
        self.root.canvas.tag_bind(self.ID, '<Button-2>', self.pressedR)

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
                self.root.lg.lattice[self.x, self.y] = State.infect.value
            else:
                color = susCol
                self.root.lg.lattice[self.x, self.y] = State.suscept.value
        self.root.canvas.itemconfig(self.ID, fill=color)

    def pressedR(self, event):
        # toggle        
        if self.live == State.suscept.value:
            color = blockCol
            self.root.lg.lattice[self.x, self.y] = State.block.value
        else:
            color = susCol
            self.root.lg.lattice[self.x, self.y] = State.suscept.value
        self.root.canvas.itemconfig(self.ID, fill=color)

class TopWindow:
    
    def show_window(self, title="title", *args):
        self.root = Tk()
        self.root.title(title)
        frames = []

        # Frame Button
        for i, arg in enumerate(args):
            frames.append(Frame(self.root, padx=5, pady=5))
            for k, v in arg:
                Button(frames[i], text=k, command=v).pack(expand=YES, fill='x')
            frames[i].pack(fill='x')

        # Config
        Label(text = 'Config').pack()
        
        # Grid(Radionbutton)
        self.tmp_grid = BooleanVar()
        Label(text = 'Grid:').pack()
        triButton = Radiobutton(self.root, text="△", value=True, variable=self.tmp_grid, command=self.changeGrid)
        triButton.select()
        triButton.pack()
        squButton = Radiobutton(self.root, text="□", value=False, variable=self.tmp_grid, command=self.changeGrid)
        squButton.pack()

        # Model(Radionbutton)
        self.tmp_model = BooleanVar()
        Label(text = 'Model:').pack()
        SIRButton = Radiobutton(self.root, text="SIR", value=False, variable=self.tmp_model, command=self.changeModel)
        SIRButton.select()
        SIRButton.pack()
        SIRSButton = Radiobutton(self.root, text="SIRS", value=True, variable=self.tmp_model, command=self.changeModel)
        SIRSButton.pack()

        # Probability(Scale)
        self.tmp_prob = DoubleVar()
        Label(text = 'Prob(%):').pack()
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
        
        # Range(Entry)
        self.tmp_range = StringVar()
        Label(text = 'Range File Name:').pack()
        EboxRange = Entry(self.root, textvariable=self.tmp_range)
        EboxRange.insert(END, RANGE)
        EboxRange.pack()                
        EboxRange.bind('<Return>', self.changeRange)

        # HotSpot(Radiobutton)
        self.tmp_hotspot = IntVar()
        Label(text = 'HotSpot :').pack()
        HotButtonOFF = Radiobutton(self.root, text="OFF", value=False, variable=self.tmp_hotspot, command=self.setHotSpot)
        HotButtonOFF.select()
        HotButtonOFF.pack()
        HotButtonON = Radiobutton(self.root, text="ON", value=True, variable=self.tmp_hotspot, command=self.setHotSpot)
        HotButtonON.pack()

        self.root.mainloop()
        
    def changeGrid(self):
        global isTriangle
        isTriangle = self.tmp_grid.get()

    def changeModel(self):
        global isSIRS
        isSIRS = self.tmp_model.get()

    def changeBeta(self, b):
        global beta
        beta = float(b)/100.0

    def changeRectime(self, event):
        global RecTime
        RecTime = int(self.tmp_rectime.get())

    def changeSustime(self, event):
        global SusTime
        SusTime = int(self.tmp_sustime.get())

    def changeRange(self, event):
        global RANGE, SettingArea
        RANGE = self.tmp_range.get()
        SettingArea = False if RANGE == "" else True

    def setHotSpot(self):
        global isSetHotSpot        
        isSetHotSpot = self.tmp_hotspot.get()

# ステータス表示用ウィンドウ（未完成）
# class ShowStatus:

#     def __init__(self, lg):
#         self.root = Tk()
#         self.root.title("Status")
#         Label(self.root, text=STATUS)
#         self.root.bind_all('<1>', self.show_status)
        
#     def show_status(self, event):
#         self.label.configure(text = STATUS)
        
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
        self.lg = SIRmodel(L, p=0, pattern=None)
        self.DrawCanvas = Draw_canvas(self.lg, self.lg.L)

    def randSet(self):
        if 'self.lg.loop' in locals():
            self.pause()
        self.lg = SIRmodel(L, p=prob, pattern=None)
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
