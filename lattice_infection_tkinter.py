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

# Enum
class State(Enum):
    suspect = 0
    infect = 1
    recover = 2

# Color Setting
susCol = "white"
infCol = "red"
recCol = "blue"

# Params

# Probability Setting
beta = 0.1
prob = 0.001 #First infected probability

# Time
Tmax = 2000
RecTime = 5

# Size
L = 200
default_size = 1080  # default size of canvas

# Effective Area
center = (100,100)
radius = 50

class SIRmodel:

    def isRange(self, x, y):
        return (x - center[0])**2 + (y - center[1])**2 < radius**2

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
    
    def progress(self, canvas_update, canvas_dataReload, update):
        t = 0
        self.loop = True
        past_lattices = []
        while self.loop:
            try:
                past_lattice = self.lattice.copy()
                past_lattices.append(past_lattice)
                
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
                            if self.lattice[m,n-1] == State.infect.value:
                                neighber += 1
                            if self.lattice[m+1,n] == State.infect.value:
                                neighber += 1
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
                    
                    if self.lattice[x, y] == State.suspect.value:
                        color = susCol
                    elif self.lattice[x, y] == State.infect.value:
                        color = infCol
                    else:
                        color = recCol                        
                        
                    canvas_update(x, y, color)
                update()
                # time.sleep(0.1)          

                # 状態更新
                t += 1
                if t > Tmax:
                    self.loop = False

                # 状態表示
                canvas_dataReload()
                
            except KeyboardInterrupt:
                print("stopped.")
                break

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
        self.c = self.canvas.create_rectangle
        self.update = self.canvas.update
        self.rects = dict()
        
        for y in range(1, self.L + 1):
            for x in range(1, self.L + 1):
                if self.lg.lattice[x, y] == State.infect.value:
                    live = State.infect.value
                else:
                    live = State.suspect.value
                    tag = "%d %d" % (x, y)
                self.rects[tag] = Rect(x, y, live, tag, self)
        self.canvas.pack()
        
    def canvas_update(self, x, y, color):
        try:
            print(self.rects)
            v = self.rects["%d %d" % (x, y)]
            v.root.canvas.itemconfig(v.ID, fill=color)
        except:
            hoge = 1

    def canvas_dataReload(self):
        tmp = []
        for i in range(self.L):
            for j in range(self.L):
                tmp.append(self.lg.lattice[i,j])
        count_dict = collections.Counter(tmp)
        for k,v in count_dict.items():
            print(v, end="\t")
        print()
        #     StateShow.pack()

class Rect:

    def __init__(self, x, y, live, tag, root):
        self.root = root
        self.x = x
        self.y = y
        self.live = live
        if live == State.suspect.value:
            color = susCol
        elif live == State.infect.value:
            color = infCol
        else:
            color = recCol
        self.ID = self.root.c(2*(x-1)*self.root.r + self.root.margin,
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
                             (('start', self.start),
                              ('pause', self.pause),
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
        self.lg.progress(self.DrawCanvas.canvas_update, self.DrawCanvas.canvas_dataReload, self.DrawCanvas.update)
        
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
        try:
            self.pause()
            sys.exit()
        except:
            sys.exit()

if __name__ == '__main__':

    app = Main()
