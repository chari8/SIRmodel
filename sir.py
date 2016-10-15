#! /usr/bin/env python
# -*- coding:utf-8 -*-
#
# written by ssh0, September 2014.
## Parameters and definitions

from tkinter import *
import numpy as np
import sys
import collections
import math
from enum import Enum

## ---------- Parameters ---------------
# Flags
isTriangle = True
isSIRS = False
settingAreaMode = 0
isSetHotSpot = False

# Probability Setting
beta = 0.3 # Rate of Infection
prob = 0.001 # Primitive infection probability

# Time
Tmax = 1000
RecTime = 10
SusTime = 10

# Size
L = 150
default_size = 1080  # default size of canvas

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

import sirmodel
import draw_canvas
import poly
import topwindow

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
        triButton.select()
        triButton.pack(anchor=W)
        squButton.pack(anchor=W)
        # triButton.pack(sticky=W)
        # squButton.pack(sticky=E)


        # Model(Radiobutton)
        self.tmp_model = BooleanVar()
        Label(text = 'Model:').pack()
        SIRButton = Radiobutton(self.root, text="SIR", value=False, variable=self.tmp_model, command=self.changeModel)
        SIRButton.select()
        SIRButton.pack(anchor = W)
        SIRSButton = Radiobutton(self.root, text="SIRS", value=True, variable=self.tmp_model, command=self.changeModel)
        SIRSButton.pack(anchor = W)

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
