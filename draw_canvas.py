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

        #スクロールバー
        # ybar = Scrollbar(self.sub, orient=VERTICAL)
        # ybar.config(command=self.canvas.yview)
        # ybar.pack(side=RIGHT, fill=Y)
        # self.canvas.config(yscrollcommand=ybar.set)
        
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
                
        self.canvas.pack(side=LEFT, expand=YES, fill=BOTH)
        
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
