import numpy as np
import matplotlib.pyplot as plt

import os
import sys
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../Search-based Planning/")
from Search_3D.env3D import env
from Search_3D import Astar3D
from Search_3D.utils3D import StateSpace, getDist, getNearest, getRay, isinbound, isinball, isCollide, children, cost, initcost
from Search_3D.plot_util3D import visualization


class D_star(object):
    def __init__(self,resolution = 1):
        self.Alldirec = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1],
                                  [-1, 0, 0], [0, -1, 0], [0, 0, -1], [-1, -1, 0], [-1, 0, -1], [0, -1, -1],
                                  [-1, -1, -1],
                                  [1, -1, 0], [-1, 1, 0], [1, 0, -1], [-1, 0, 1], [0, 1, -1], [0, -1, 1],
                                  [1, -1, -1], [-1, 1, -1], [-1, -1, 1], [1, 1, -1], [1, -1, 1], [-1, 1, 1]])
        self.env = env(resolution = resolution)
        self.X = StateSpace(self.env)
        self.x0, self.xt = getNearest(self.X, self.env.start), getNearest(self.X, self.env.goal)
        self.b = defaultdict(lambda: defaultdict(dict))# back pointers every state has one except xt.
        self.OPEN = {} # OPEN list, here use a hashmap implementation. hash is point, key is value 
        self.h = self.initH() # estimate from a point to the end point
        self.tag = self.initTag() # set all states to new
        self.V = set()# vertice in closed
        # initialize cost set
        # self.c = initcost(self)
        # for visualization
        self.ind = 0
        self.Path = []
        self.done = False

        

    def initH(self):
        # h set, all initialzed h vals are 0 for all states.
        h = {}
        for xi in self.X:
            h[xi] = 0
        return h

    def initTag(self):
        # tag , New point (never been in the OPEN list)
        #       Open point ( currently in OPEN )
        #       Closed (currently in CLOSED)
        t = {} 
        for xi in self.X:
            t[xi] = 'New'
        return t

    def get_kmin(self):
        # get the minimum of the k val in OPEN
        # -1 if it does not exist
        if self.OPEN:
            minv = np.inf
            for v,k in enumerate(self.OPEN):
                if v < minv: minv = v
            return minv
        return -1

    def min_state(self):
        # returns the state in OPEN with min k(.)
        # if empty, returns None and -1
        # it also removes this min value form the OPEN set.
        if self.OPEN:
            minv = np.inf
            for v,k in enumerate(self.OPEN):
                if v < minv: mink, minv = k, v
            return mink, self.OPEN.pop(mink)
        return None, -1
    
    def insert(self, x, h_new):
        # inserting a key and value into OPEN list (x, kx)
        # depending on following situations
        if self.tag[x] == 'New':
            kx = h_new
        if self.tag[x] == 'Open':
            kx = min(self.OPEN[x],h_new)
        if self.tag[x] == 'Closed':
            kx = min(self.h[x], h_new)
        self.OPEN[x] = kx
        self.h[x],self.tag[x] = h_new, 'Open'
            
    def process_state(self):
        x, kold = self.min_state()
        self.tag[x] = 'Closed'
        self.V.add(x)
        if x == None: return -1
        if kold < self.h[x]: # raised states
            for y in children(self,x):
                a = self.h[y] + cost(self,y,x)
                if self.h[y] <= kold and self.h[x] > a:
                    self.b[x], self.h[x] = y , a
        elif kold == self.h[x]:# lower
            for y in children(self,x):
                bb = self.h[x] + cost(self,x,y)
                if self.tag[y] == 'New' or \
                    (self.b[y] == x and self.h[y] != bb) or \
                    (self.b[y] != x and self.h[y] > bb):
                    self.b[y] = x
                    self.insert(y, bb)
        else: 
            for y in children(self,x):
                bb = self.h[x] + cost(self,x,y)
                if self.tag[y] == 'New' or \
                    (self.b[y] == x and self.h[y] != bb):
                    self.b[y] = x
                    self.insert(y, bb)
                else:
                    if self.b[y] != x and self.h[y] > bb:
                        self.insert(x, self.h[x])
                    else:
                        if self.b[y] != x and self.h[y] > bb and \
                            self.tag[y] == 'Closed' and self.h[y] == kold:
                            self.insert(y, self.h[y])
        return self.get_kmin()

    def modify_cost(self,x,y,cval):
        # TODO: implement own function
        # self.c[x][y] = cval
        # if self.tag[x] == 'Closed': self.insert(x,self.h[x])
        # return self.get_kmin()
        pass

    def path(self):
        path = []
        x = self.x0
        start = self.xt
        while x != start:
            path.append([np.array(x), np.array(self.b[x])])
            x = self.b[x]
        return path

    def run(self):
        # put G (ending state) into the OPEN list
        self.OPEN[self.xt] = 0
        # first run
        while True:
            #TODO: self.x0 = 
            self.process_state()
            visualization(self)
            if self.tag[self.x0] == "Closed":
                break
            self.ind += 1
        self.Path = self.path()
        self.done = True
        visualization(self)
        # plt.show()
        # when the environemnt changes over time
        s = tuple(self.env.start)
        while s != self.xt:
            if s == tuple(self.env.start):
                s = self.b[self.x0]
            else: 
                s = self.b[s]
            self.process_state()
            self.env.move_block(a=[0,0,0.1],s=0.5,mode='translation')
            self.Path = self.path()
            visualization(self)
            self.ind += 1
        

        
if __name__ == '__main__':
    D = D_star(1)
    D.run()