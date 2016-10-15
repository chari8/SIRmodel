# SIRmodel

class SIRmodel:

    def __init__(self, L=30, p=None, pattern=None):
        self.L = L  # lattice size
        self.illTime = np.zeros([self.L + 2, self.L + 2])

        # 範囲設定
        global settingAreaMode
        self.lst = []
        if settingAreaMode > 0:
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
            
        self.lattice = np.zeros([self.L + 2, self.L + 2], dtype=int)    
        if p > 0:
            lattice = np.random.random([self.L + 2, self.L + 2])
            
            # 初期感染点の設置
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
                    self.lattice[m,n] = State.block.value

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
        print(dots)
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

        if not settingAreaMode == 1:
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
