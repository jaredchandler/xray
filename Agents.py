
import re
from collections import defaultdict
import copy
import sys
import argparse
import subprocess
import functools
import json

foldl = lambda func, acc, xs: functools.reduce(func, xs, acc)



class User:
    def __init__(self,u,g):
        self.u = u
        self.g = g

    def __str__(self):
        return "( " + self.u + " )"
    def __eq__(self, other):
        return self.u == other.u and self.g == other.g


class Agent:

    def __init__(self,fname):

        closure_users,closure_groups = self.load(fname)
        self.closure_users   = closure_users 
        self.closure_groups  = closure_groups
        #self.universe = [self.mkUser(username) for username in self.closure_users.keys()]
        self.universe        = set([self.mkUser(username) for username in self.closure_users.keys()])


    def load(self,fname):
        # Groups file should have records in the formal
        # username : group1 group2 group3
        closure_users  = defaultdict(lambda :(None,[]))
        closure_groups = defaultdict(lambda: set())
        print(fname)
        if fname != None:
            f = open(fname)
            group_str = f.read().strip()
            f.close()

       

            for l in group_str.split("\n"):
                u,g = [p.strip() for p in l.split(":")]
                grplist = g.split(" ")
                for grp in grplist:
                    closure_groups[grp].add(u)
                closure_users[u] = (u,grplist)

        else:
            print("*** Warning : No Groups File provided. Users will not be associated with groups. ***")

        return closure_users,closure_groups

    def mkUser (self,username):

        u,g = self.closure_users[username]

        return ('user',u)

    def mkUserSet(self,username):
        return set([self.mkUser(username)])

    def mkGroupSet (self,groupname):
        return set([self.mkUser(username) for username in self.closure_groups[groupname]])

    def mkGroup(self,groupname):
        return [('user',username) for username in self.closure_groups[groupname]]

    def union(self,xs):
        if type(xs) != type([]):
            return xs
        else:
            head = xs[0]
            tail = xs[1:]
            for t in tail:
                head = head.union(t)
            return head


    def intersection(self,xs):
        if type(xs) != type([]):
            return xs
        else:
            head = xs[0]
            tail = xs[1:]
            for t in tail:
                head = head.intersection(t)
            return head



    def compliment(self,a):
        return self.difference(self.universe,a)

    def difference(self,a,b):
        return a.difference(b)


