class Poly:

    def __init__(self, x, y, live, tag, root):
        self.root = root
        self.x = x
        self.y = y
        self.live = live
        color = enum2color[live]
        size = 2.5
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

