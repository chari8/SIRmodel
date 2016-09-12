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
TriMode = True

# Probability Setting
beta = 0.1 # Rate of Infection
prob = 0.001 # Primitive infection probability

# Time
Tmax = 2000
RecTime = 5

# Size
L = 100
default_size = 1080  # default size of canvas

# Effective Area
# Round
center = (100,100)
radius = 50

## ---------- End ---------------

# State Setting
class State(Enum):
    suspect = 0
    infect = 1
    recover = 2

# Color Setting
susCol = "white"
infCol = "red"
recCol = "blue"

# Enum2Color
enum2color = [susCol, infCol, recCol]

# Useful functions
def isEven(x):
    return x%2 == 0

def isOdd(x):
    return not isEven(x)

def isDelta(x,y):
    return (isEven(x) and isEven(y)) or (isOdd(x) and isOdd(y))

def isNabla(x,y):
    return not isDelta(x,y)

class SIRmodel:

    def isRange(self, x, y):
        # return (x - center[0])**2 + (y - center[1])**2 < radius**2
        return True

    def __init__(self, L=30, p=None, pattern=None):
        self.L = L  # lattice size
        self.illTime = np.zeros([self.L + 2, self.L + 2])
        if p > 0:
            lattice = np.random.random([self.L + 2, self.L + 2])
            self.lattice = np.zeros([self.L + 2, self.L + 2], dtype=int) 
            for i in range(L+2):
                for j in range(L+2):

                    # 範囲指定
                    if not self.isRange(i,j):
                        continue
                    
                    if lattice[i,j] < p:
                        self.lattice[i,j] = State.infect.value
                    else:
                        self.lattice[i,j] = State.suspect.value
            self.lattice[0, :] = self.lattice[self.L+1, :] = State.suspect.value
            self.lattice[:, 0] = self.lattice[:, self.L + 1] = State.suspect.value
        else:
            self.lattice = np.zeros([self.L + 2, self.L + 2], dtype=int)
            if pattern:
                for x, y in pattern:
                    self.lattice[x, y] = State.infect.value
        self.past_lattices = []
        self.t = 0
    
    def progress(self, canvas_update, canvas_displayStatus, update):
        self.loop = True
        self.illTime[:, :] = 0
        while self.loop:
            try:
                past_lattice = self.lattice.copy()
                self.past_lattices.append(past_lattice)
                
                # 隣接格子点の判定
                for m in range(1, self.L + 1):
                    for n in range(1, self.L + 1):

                        # 範囲指定
                        if not self.isRange(m,n):
                            continue
                        
                        if self.lattice[m,n] == State.suspect.value:
                            ## 感染判定
                            
                            # 周囲のinfect.value数を調べる
                            neighber = 0
                            if self.lattice[m-1,n] == State.infect.value:
                                neighber += 1
                            if self.lattice[m+1,n] == State.infect.value:
                                neighber += 1
                            if not(TriMode and isDelta(m,n)): 
                                if self.lattice[m,n-1] == State.infect.value:
                                    neighber += 1
                            if not(TriMode and isNabla(m,n)):
                                if self.lattice[m,n+1] == State.infect.value:
                                    neighber += 1

                            # 各感染者から感染するか計算    
                            for i in range(neighber):
                                if np.random.random() < beta:
                                    self.lattice[m,n] = State.infect.value

                        elif self.lattice[m,n] == State.infect.value:
                            
                            # State = InfectならばillTimeをインクリメント
                            # 一定時間でInfectからRecoverへ
                            if self.illTime[m,n] > RecTime:
                                self.lattice[m,n] = State.recover.value
                            else:
                                self.illTime[m,n] += 1

                        else:
                            # State = Recoverdならばスルー
                            continue
                
                # 描画の更新
                changed_rect = np.where(self.lattice != past_lattice)
                for x, y in zip(changed_rect[0], changed_rect[1]):
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
        self.past = []
        
        for y in range(1, self.L + 1):
            for x in range(1, self.L + 1):
                live = self.lg.lattice[x,y]
                tag = "%d %d" % (x, y)
                if TriMode:
                    self.rects[tag] = Tri(x, y, live, tag, self)
                else:
                    self.rects[tag] = Rect(x, y, live, tag, self)                   
                self.canvas.pack()
        
    def canvas_update(self, x, y, color):
        try:
            v = self.rects["%d %d" % (x, y)]
            v.root.canvas.itemconfig(v.ID, fill=color)
        except:
            pass
        
    def canvas_displayStatus(self, lat):
        tmp = []
        for i in range(1, self.L+1):
            for j in range(1,self.L+1):
                tmp.append(lat[i,j])
        count_dict = collections.Counter(tmp)
        if count_dict != self.past:
            for k,v in count_dict.items():
                print(v, end="\t")
            print()
            self.past = count_dict

class Rect:

    def __init__(self, x, y, live, tag, root):
        self.root = root
        self.x = x
        self.y = y
        self.live = live
        color = enum2color[live]
        self.ID = self.root.cr(2*(x-1)*self.root.r + self.root.margin,
                              2*(y-1)*self.root.r + self.root.margin,
                              2*x*self.root.r + self.root.margin,
                              2*y*self.root.r + self.root.margin,
                              outline="#202020", fill=color, tag=tag)
        self.root.canvas.tag_bind(self.ID, '<Button-1>', self.pressed)

    def pressed(self, event):

        # toggle
        if self.live == State.suspect.value:
            color = infCol
        else:
            color = susCol
        self.root.lg.lattice[self.x, self.y] = State.infect.value
        self.root.canvas.itemconfig(self.ID, fill=color)

class Tri:

    def __init__(self, x, y, live, tag, root):
        self.root = root
        self.x = x
        self.y = y
        self.live = live
        color = enum2color[live]
        size = 2

        ## Divide M line or W line
            
        if isDelta(x,y):
            # △
            x /= 2
            self.ID = self.root.ct(size*x*self.root.r + self.root.margin,
                              size*y*self.root.r + self.root.margin,
                              size*(x+0.5)*self.root.r + self.root.margin,
                              size*(y-1)*self.root.r + self.root.margin,
                               size*(x+1)*self.root.r + self.root.margin,
                              size*y*self.root.r + self.root.margin,
                              outline="#202020", fill=color, tag=tag)
        else:
            # ▽
            x /= 2
            self.ID = self.root.ct(size*x*self.root.r + self.root.margin,
                              size*(y-1)*self.root.r + self.root.margin,
                              size*(x+0.5)*self.root.r + self.root.margin,
                              size*y*self.root.r + self.root.margin,
                               size*(x+1)*self.root.r + self.root.margin,
                              size*(y-1)*self.root.r + self.root.margin,
                              outline="#202020", fill=color, tag=tag)
        self.root.canvas.tag_bind(self.ID, '<Button-1>', self.pressed)

    def pressed(self, event):

        # toggle
        if self.live == State.suspect.value:
            color = infCol
        else:
            color = susCol
        self.root.lg.lattice[self.x, self.y] = State.infect.value
        self.root.canvas.itemconfig(self.ID, fill=color)

class TopWindow:

    def show_window(self, title="title", *args):
        self.root = Tk()
        self.root.title(title)
        frames = []
        for i, arg in enumerate(args):
            frames.append(Frame(self.root, padx=5, pady=5))
            for k, v in arg:
                Button(frames[i], text=k, command=v).pack(expand=YES, fill='x')
            frames[i].pack(fill='x')
        self.root.mainloop()

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
        self.lg = SIRmodel(L, p=0, pattern=None)        
        self.DrawCanvas = Draw_canvas(self.lg, self.lg.L)

    def randSet(self):
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
        sys.exit()

if __name__ == '__main__':

    app = Main()
