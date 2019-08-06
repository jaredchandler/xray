
import re
from collections import defaultdict
import copy
import sys
import argparse
import subprocess
import functools
import json
from settings import *
foldl = lambda func, acc, xs: functools.reduce(func, xs, acc)


#-------HELPERS------------



# used to determine if a permission group has execute permission
def hasx(s):
    return s[-1]== "x" or s[-1] == "s" or s[-1] == "S" 

# used to determine if a permission group has read permissions
def hasr(s):
    return s[0]== "r"

# user to determine if a permission group has write permissions
def hasw(s):
    return s[1]== "w"

# create gset
def gset(gs):
    return (sorted(gs),[])

# adds grp to gs, returns new gset
def gsetAdd(gs,grp):
    g,e = gs
    if grp not in g:
        return (sorted(g + [grp]),e)
    else:
        return gs

# adds grp to exclude, returns new gset
def gsetExclude(gs,grp):
    g,e = gs
    if grp not in e:
        return (g,sorted(e + [grp]))
    else:
        return gs

# string representation of gset
def gsetStr(gs):
    g,e = gs
    return "( + " + ",".join(sorted(map(str,g))) + " | - " + ",".join(sorted(map(str,e))) + " )"

# get groups from gset
def gsetGroups(gs):
    g,e = gs
    return g

# get excludes from gset
def gsetExcludes(gs):
    g,e = gs
    return e

# handles list append
def nsetAppend(ns,n):
    if n in ns:
        return ns
    else:
        return ns + [n]

# filter contradictions
# anything with a group in both the required and excluded is ommitted
def nsetRemoveContradictions(nset):
    res = []
    for gs in nset:
        
        e = gsetExcludes(gs)
        g = gsetGroups(gs)

        # you can't BE two users at one. you CAN be NOT two or more users at once.
        qty_users = [u for u in list(set(g)) if u[:4] == "USER"]
        if len(qty_users) <= 1:
            
            # if the intersection of required and excludes is empty set
            # then no member is in both sets
            # and there is no contradiction 
            r =set(g).intersection(set(e))
            if r==set():
                res.append(gs)
    return res

other = "EVERYONE"


#enumerate permissions
def enump(user,user_x,group,group_x,other_x,pset):
    nset = []
    #requires user to be in list
    user_plus = lambda gs:gsetAdd(gs,user)

    #requires user to not be in list
    user_minus = lambda gs:gsetExclude(gs,user)


    group_plus     = lambda gs:gsetAdd(gs,group)
    group_minus    = lambda gs:gsetExclude(gs,group)
    everyone_plus  = lambda gs:gsetAdd(gs,other)
    everyone_minus = lambda gs:gsetExclude(gs,other)

    t = (user_x,group_x,other_x)


    for gs in pset:
        if t == (True,True,True):
            # U+ G+ E+
            #      V U+
            #      V U- G+
            #      V U- G- E+
            nset = nsetAppend(nset,user_plus(gs))
            nset = nsetAppend(nset,user_minus(group_plus(gs)))
            nset = nsetAppend(nset,user_minus(group_minus(everyone_plus(gs))))

        elif t == (True,True,False):
            # U+ G+ E-
            #     V U+
            #     V U- G+
            nset = nsetAppend(nset,user_plus(gs))
            nset = nsetAppend(nset,user_minus(group_plus(gs)))
        elif t == (True,False,True):
            # U+ G- E+
            #     V U+
            #     V U- G- E+
            nset = nsetAppend(nset,user_plus(gs))
            nset = nsetAppend(nset,user_minus(group_minus(everyone_plus(gs))))

        elif t == (True,False,False):
            # U+ G- E-
            #     V U+
            nset = nsetAppend(nset,user_plus(gs))

        elif t == (False,True,True):
            # U- G+ E+
            #     V U- G+
            #     V U- G- E+
            nset = nsetAppend(nset,user_minus(group_plus(gs)))
            nset = nsetAppend(nset,user_minus(group_minus(everyone_plus(gs))))
                
        elif t == (False,True,False):
            # U- G+ E-
            #     V U- G+
            nset = nsetAppend(nset,user_minus(group_plus(gs))) 

        elif t == (False,False,True):
            # U- G- E+
            #     V U- G- E+
            nset = nsetAppend(nset,user_minus(group_minus(everyone_plus(gs))))

        elif t == (False,False,False):
            nset = [] 
        else:
            pass



    return nset


#general condition function

# interprets a condition at a node based on input from higher level
# stores result in note.

def condition(label,obj_f,cn):

    # get parent constraints
    parent_conf = cn.getParentConf(label)

   
    
    #user and group for this node
    user = "USER_" + cn.user
    group = "GROUP_" + cn.group  

    # objective function (node,perms -> boolean)
    user_p  = obj_f(cn,cn.userperms)
    group_p = obj_f(cn,cn.groupperms)
    other_p = obj_f(cn,cn.otherperms)

    #create our enumeration of configuration
    nset = enump(user,user_p,group,group_p,other_p,parent_conf)
   
    #remove contradictions
    cset = nsetRemoveContradictions(nset)

    cn.setConf(label,cset)
    return cset


# if this is a folder, require x, 
# if a file, require r
# captures idea of being able to get to the contents
def traversable_f(cn,perm):
    if cn.isDir():
        return hasx(perm)
    else:
        return hasr(perm)

# if this is a folder, require r and x, 
# if a file, require r
# captures idea of being able to get to the contents without prior knowledge
def discoverable_f(cn,perm):
    if cn.isDir():
        return hasx(perm) and hasr(perm)
    else:
        return hasr(perm)
 
# if a folder you need x, if a file your need write.
def editable_f(cn,perm):
    if cn.isDir():
        return hasx(perm)
    else:
        if cn.isFile():
            return hasw(perm)
        else:
            return False

def executable_f(cn,perm):
    if cn.isDir():
        return hasx(perm)
    else:
        return hasx(perm)

#---------------------------------------------------------
#---------------------------------------------------------

# get configurations which satisfy this node
#nset = pt3(cn,pset)

#cset = [Permissionr.traversableCondition,Permissionr.discoverableCondition,Permissionr.editableCondition]

discoverableCondition = lambda cn: condition("discoverable",discoverable_f,cn)
traversableCondition  = lambda cn: condition("traversable", traversable_f, cn)
editableCondition     = lambda cn: condition("editable", editable_f, cn)
executableCondition   = lambda cn: condition("executable", executable_f, cn)
#--------------------------




class Node:

    #get our handle to an outside datastructure
    #tree = tree

    def __init__(self,tree,path):
        self.tree = tree
        self.full_path = path
        parts = path.split("/")
        self.rec = None
        self.configurations = []
        self.configurations_sets = {}
        #invariant, depth = number of / slashes 
        #figure out depth
      
        if len(parts) > 1 and parts[1] != "":
            self.path = path
            self.depth = len(parts)-1
            self.parent = "/".join(parts[:-1])
            self.tree.get(self.parent).addChild(self.path)
        else:
            #handle the root case
            self.path = parts[0]
            self.depth = 0
            self.parent = None
            self.tree.root = self

        #keep track of children as a set
        #we only use their path
        self.children = set()
        self.effectiveperms = defaultdict(lambda:"---")

        #register this new node in the class variable tree
        self.tree.add(self)

    #add a child directory
    def addChild(self,path):
        self.children.add(path)

    # store the record information in a node
    #add the complete record for this node
    def setRec(self,rec):
        self.rec = rec
        self.group = rec["group"]
        self.user = rec["user"]
        self.groupperms = rec["groupperms"]
        self.userperms = rec["userperms"]
        self.otherperms = rec["otherperms"]

    #get a list of child nodes
    def getChildren(self):
        return [self.tree.get(child) for child in sorted(self.children)]

    #give back instance of parent node
    def getParent(self):
        if self.parent:
                return self.tree.get(self.parent)
        else:
            return None




    # get a labelled configuration
    def getConf(self,label):
        if label not in self.configurations_sets.keys():
            #initialize to an empty set
            self.configurations_sets[label] = [gset([])]
        return self.configurations_sets[label]

    # set a labelled configuration
    def setConf(self,label,conf):
        self.configurations_sets[label] = conf

    # get a parents configuration by label
    def getParentConf(self,label):
        p = self.getParent()
        if p:
            return p.getConf(label)
        #no parent. must be root node. return empty configuration for any label
        else:
            return [gset([])]


    # boolean, are we a directory or not?
    def isDir(self):
        return self.rec["dir"]
    def isFile(self):
        return self.rec["file"]

    #return the string representation of our configuration
    def conf(self):
        if self.configurations != []:
            cstr= ""
            #cstr = "" +self.path + "\n"
            for x in self.configurations:
                g,e = x
                #dir or file flag
                if self.isDir():
                    d = "d"
                else:
                    d = "f"
                cstr+= self.path+"\t" + d + "\t" + " ".join(g + ["NOT_" + s for s in e]) + "\n" 
            return cstr
        else: 
            return None

    def pprint(self,g,e):
        everyone = ",".join([u for u in g if "EVERYONE" in u] )
        user =  ",".join([u for u in g if "USER_" in u])
        groups =  ",".join([u for u in g if "GROUP_" in u])
        not_users =  ",".join([""+u for u in e if "USER_" in u])
        not_groups =  ",".join([""+u for u in e if "GROUP_" in u])
        return "all:[" + everyone + "] user:[" + user + "] group:[" +groups+ "]" + " not_users:[" + not_users+ "] not_groups:[" + not_groups +"]"

    # given a label, gets back a nice string with the label, path and constraints
    def confByLabel(self,label):
        if self.getConf(label) != []:
            cstr= ""
            
            for x in self.getConf(label):
                g,e = x
                if self.isDir():
                    d = "d"
                else:
                    d = "f"
                #old version
                #cstr+= label+"\t"+ d + "\t"+self.path+"\t" + " ".join(g + ["NOT_" + s for s in e]) + "\n" 
                cstr+= label+"\t"+ d + "\t"+self.path+"\t" + self.pprint(g,e) + "\n" 

            return cstr
        else: 
            return None


    def __str__(self):
        pad = "    "*self.depth
        pad = ""
        strep = "Node(" + self.path + " : " + self.rec["perms"] + ")"
     
        cstr = ""

        return strep

    def streff(self,u,g):
        pad = "    "*self.depth
        pad = ""
        strep=  pad+ ""+" "+ str(self.depth)+ " " + self.rec["perms"] + " " + self.rec["user"] + " " + self.rec["group"]+ " "+ self.effectiveperms[u,g] +"\t"+self.path+""
        cstr = ""

        return strep








# this is the class we use to keep track of stuff
class Tree:



# this is the structure we use for directories


    

    def __init__(self):
        self.nodes = defaultdict(lambda:None)
        self.root = None
        self.load()

    def add(self,node):
        self.nodes[node.path] = node
        return self.nodes[node.path]

    def get(self,path):
        if self.nodes[path] == None:
            #print("didnt exist")
            
            self.nodes[path] = Node(self,path)
        return self.nodes[path] 

    # this converts a line of find output into a record with appropriate fields for our computation
    def line2rec(self,line):
        rec = {}
        labels = ['inode', 'blocks', 'perms', 'parmlinks', 'user', 'group', 'size', 'month', 'day', 'tm', 'path']

        parts = re.sub(" +"," ",line).split(" ")
        
        for a,b in zip(labels,parts):
            rec[a] = b

        #store original line   
        rec["raw"] = line 

        #pull apart perms
        p = rec["perms"]

        u_p = p[1:4]
        g_p = p[4:7]
        o_p = p[7:10]
        rec["userperms"] = u_p
        rec["groupperms"] = g_p
        rec["otherperms"] = o_p
        
        #is this a directory
        if p[0] == "d":
            rec["dir"] = True
            rec["file"] = False
            rec["link"] = False
        #else must be link or file
        else:
            if p[0] == "l":
                rec["dir"] = False
                rec["file"] = False
                rec["link"] = True
            #must be file
            else:
                rec["dir"] = False
                rec["file"] = True
                rec["link"] = False
        

        #what is the label
        rec["type"] = p[0]
        return rec
    #ldap-   
    def load(self):

        global args

        # if we are getting input from running find
        if args.rootpath:

            self.rootpath = args.rootpath.strip()

            #strip the trailing slash. 
            if self.rootpath[-1] == "/":
                self.rootpath = self.rootpath[:-1]

        # if we are getting input from a file
        if args.fname:
            f = open(args.fname)
            lines_raw = f.read().strip()
            f.close()

            lines = lines_raw.split("\n")

            # set root path as first thing in file
            self.rootpath = lines[0].split(" ")[-1]
            #print("self.rootpath",self.rootpath)
            if self.rootpath[-1] == "/":
                self.rootpath = self.rootpath[:-1]

        # if a root path has been specified, use it
        if args.rootpath:

            self.rootpath = args.rootpath.strip()

            #strip the trailing slash. 
            if self.rootpath[-1] == "/":
                self.rootpath = self.rootpath[:-1]       


        # build our set of records
        self.recs = []
        for line in lines:
            r = self.line2rec(line)
            self.recs.append(r)
            n = Node(self,r["path"]).setRec(r)
            
        #build sets of users and gorups
        self.users = set()
        self.groups = set()

        for rec in self.recs:
            self.users.add(rec["user"])
            self.groups.add(rec["group"])




class Permissionr:




        
    # recursively calls pt3 on each node in the tree. 
    def trav(self,cn):


        #---------------------------------------------------------
        #---------------------------------------------------------

    
        # this is a list of functions
        cset = [traversableCondition,discoverableCondition,editableCondition,executableCondition]
        for c_f in cset:
            c_f(cn)

        # do stuff to print them out

        for label in sorted(cn.configurations_sets.keys()):
            c = cn.confByLabel(label)
            if c:
                #print( c[:-1])
                pass
                


        # recurse onto children
        if cn.rec["dir"]:
            if cn.getChildren()!=[]:
                for c in cn.getChildren():
                    self.trav(c)

    # recursively calls pt3 on each node in the tree. 


    # given y should be satisfied by agsuser and argsgroups
    # for example, if everyone does not require a user and requires no groups
    # any input y should satisfy that condition

    # y is a constraint set from the tree. 
    # g = positive constraints
    # e = negative constraints


def pred(y,argsuser,argsgroups):

    g,e = y

    req_users = set([u for u in g if "USER_" in u])
    req_groups = set([u for u in g if "GROUP_" in u])
    ex_users = set([u for u  in e if "USER_" in u])
    ex_groups = set([u for u in e if "GROUP_" in u])

    #print(req_users,req_groups,ex_users,ex_groups)
    
   
    user = argsuser
    #user = "f"

    if user:
        user = "USER_" + user
        myuser = set([user])
    else:
        myuser = set()

    if argsgroups != []:
        mygroups = set(["GROUP_"+x for x in argsgroups])
    else:
        mygroups = set(argsgroups)
    

    #print(myuser,req_users,req_groups,ex_users,ex_groups)
    #if user is defined
    #user cant be excluded

    if user:
        if req_users == set():
            b1= True
        else:
            b1 = user in req_users
    #if user isn't defined, we don't care
    else:
        b1 = True



    # are all the req_users presents in myser?
    #
    # Edge cases: both are 
    #                      user  req_user
    #                      set() set()  True
    #                     {user} set()  True
    #                      set() {user} False 
    #                    {user1} {user2} False
    #

    b2 = req_users.issubset(myuser)

    # are all the req_groups present in mygroups?
    b3 = req_groups.issubset(mygroups)

    # is there no intersection between mygroups and ex_groups
    b4 = set() == mygroups.intersection(ex_groups)

    # is the user excluded? (is there no intersection between myuser and ex_users)
    b5 = set() == myuser.intersection(ex_users)

    #print(b2,b3,b4)
    #print()
    return  b1 and b2 and b3 and b4 and b5








def pathCondition(cn,p):
    return p in cn.path

class Pred:
    def __init__(self,lbl):
        self.lbl = lbl





def mkTree():


    # this is the tree in which we our nodes register themselves
    tree = Tree()

    #get our topnode
    cn =  tree.get(tree.rootpath)
    p = Permissionr()
    p.trav(cn)
    
    return cn



