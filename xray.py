#!/usr/bin/env python2.7
from settings import *



import re
from collections import defaultdict
import copy
import sys
import argparse
import subprocess
import functools
import json

foldl = lambda func, acc, xs: functools.reduce(func, xs, acc)





from settings import *


from DirTree import *
from xray_cmd_parser import *

def padnumber(n):
    str_number=str(n)
    return '%s' % (str_number.rjust(6))

# constraints is a pair of positive and negative constraints
# argsuser is the user we want to test
# argsgroups are the groups that user is a member of
# returns a boolean

def agent_pred(constraint,argsuser,argsgroups):

    required,excluded = constraint


    # print("-------------------------====")
    # print("argsuser",argsuser)
    # print("argsgroups",argsgroups)
    # print("constrating",required,excluded)

    req_users = set([u for u in required if "USER_" in u])
    req_groups = set([u for u in required if "GROUP_" in u])
    ex_users = set([u for u  in excluded if "USER_" in u])
    ex_groups = set([u for u in excluded if "GROUP_" in u])

    #print(req_users,req_groups,ex_users,ex_groups)
    
   
    user = argsuser


    if user:
        user = "USER_" + user #convert it into constraint form
        myuser = set([user])
    else:
        myuser = set()

    if argsgroups != []:
        mygroups = set(["GROUP_"+x for x in argsgroups]) #convert into constrain form
    else:
        mygroups = set(argsgroups)
    
    #print(myuser,req_users,req_groups,ex_users,ex_groups)

    # print("user",user)
    # print("mygroups",mygroups)

    #if user is defined
    #user cant be excluded
    if user:
        if req_users == set():
            b1= True
        else:
            b1 = user in req_users # <- we check that user is in the constrain required user
    #if user isn't defined, we don't care
    else:
        if req_users == set():
            b1 = True # as no user is required
        else:
            b1 = False # the required user is not empty, but we have no user



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

    return  b1 and b2 and b3 and b4 and b5


def query(cn,agent_function,lbl,path_function):

    if path_function(cn):
        r = agent_function(cn.configurations_sets["traversable"])
        #print("\tpmap:" + str(r))
        if r:
            print("\t"+str(r)+"\t"+lbl+"\t"+cn.rec["raw"])

        else:
            print("\t"+str(r)+"\t"+lbl+"\t"+cn.rec["raw"])
    if cn.rec["dir"]:
        if cn.getChildren()!=[]:
            for c in cn.getChildren():
                query(c,agent_function,lbl,path_function)




def querytf(cn,agent_function,perm_type,lbl,path_function,tf,ff,depth_limit,show_true,show_false,xtraf,show,files):
    rows = []
    xrays = []
    a = 0
    b = 0

    json_name = cn.path
    kids = []

    if path_function(cn.path):




        r = agent_function(cn.configurations_sets[perm_type])
        #print("cn.configs",cn.configurations_sets[perm_type])
        #satisfies agent predicate
        if xtraf(cn):
            if r:
                a+=1
                tf(cn,lbl)
                #print("\t"+str(r)+"\t"+lbl+"\t"+cn.rec["raw"])

            #does not satisfy agent  predicate
            else:
                b+=1
                ff(cn,lbl)
                #print("\t"+str(r)+"\t"+lbl+"\t"+cn.rec["raw"])
  
    # if this is a directory, recurse
    if cn.rec["dir"]:

        #if we have children
        if cn.getChildren()!=[]:
            for c in cn.getChildren():

                #recursive call on children
                ab = querytf(c,agent_function,perm_type,lbl,path_function,tf,ff,depth_limit,show_true,show_false,xtraf,show,files)
                a1,b1,childname,k,crows = ab
                
                rows.extend(crows)
                a+=a1
                b+=b1

                if cn.depth < depth_limit:
                    kids.append(ab)

                # if this is at the depth limit include but do not list children
                
                if cn.depth == depth_limit:
                    kids.append((a1,b1,childname,[]))

    # if this is within our depth limit and we have something to report
    # report it.
    # if (a > 0 or b > 0 ) and cn.depth < depth_limit:
    #     print( "( " + str(a) + " , " + str(b) + " )" + "\t" + cn.rec["raw"])
    if (files == False) or ((files == True) and cn.isFile()):
        if ((show_true and a > 0) or (show_false and b > 0)) and cn.depth < depth_limit:
            #print( "( " + str(a) + " , " + str(b) + " )" + "\t" + cn.rec["raw"])
            #print( "( " + padnumber(a) + " , " + padnumber(b) + " )" + " " + cn.rec["raw"][14:])
            row = "( " + padnumber(a) + " , " + padnumber(b) + " )" + " " + cn.rec["raw"][14:]


            tmpxray =[]

            # if we want to see the configurations which allow access
            if show:
                ptot = agent_function(cn.configurations_sets[perm_type])
                for pt in cn.configurations_sets[perm_type]:
                        br = agent_function([pt])
                        #print("\t" + str(ptot) + "\t" + str(br) + "\t"+ str(pt))
                        ptpos,ptneg = pt
                        npos = ["+"+p for p in ptpos]
                        nneg = ["-"+p for p in ptneg]
                        npos.append("|")
                        npos.extend(nneg)
                        #ptr = ["+"+p for p in ptpos].extend(["-"+p for p in ptneg])
                        xrayrow = "\t Agent Sat? "  + str(br) + "\t( "+ str(" ".join(npos))+" )" 
                        tmpxray.append(xrayrow)

            tmprow = [(row,tmpxray)]
            tmprow.extend(rows)
            rows = tmprow
    return (a,b,json_name,kids,rows)





def pathCondition(cn,p):
    return p in cn.path

class Pred:
    def __init__(self,lbl):
        self.lbl = lbl



# #create a single Groupset for everyone represented as None
# init = [gset([])]

unit = lambda cn: True

def negatef(f):
    return lambda x: not f(x)



#limit by confition in path
def path(cn,x,f):
    if x in cn.path:
        return f(cn)
    else:
        return False

#limit by type of node
def nodeType(cn,x,f):
    if cn.rec["type"] == x:
        return f(cn)
    else:
        return False


# takes and x and a finuction returns function which takes a node
filterPath = lambda x,f: lambda cn: path(cn,x,f)
filterType = lambda x,f: lambda cn: nodeType(cn,x,f)

def orf(x,f,g):
    if f(x):
        return True
    else:
        return g(x)

def andf(x,f,g):
    if f(x):
        return g(x)
    else:
        return False

allOf = lambda f,g: lambda x: andf ( x, f, g )
oneOf = lambda f,g: lambda x: orf  ( x, f, g )

def conj(fs):
    return lambda x: False not in map(lambda f:f(x),fs)

funit = lambda x: False
tunit = lambda x: True


compose_orf  = lambda f,g: lambda x: orf(x,f,g)
compose_andf = lambda f,g: lambda x: andf(x,f,g)

disj = lambda fs: foldl(compose_orf,funit,fs)
conj = lambda fs: foldl(compose_andf,tunit,fs)

#foldl(lambda x,y:x.union(y),set(),recs)


def pmap(f,cns):
    # for c in cns:
    #     print("\t"+str(f(c))+ "\t" + str(c))
    return map(f,cns)


# one is true 
# one configuration does satisfy f
# this f could get through
oneIsTrue = lambda f: lambda cns: True in pmap(f,cns)

# one is false
# some configuration does not satisfy this f
# another configuration could get through
oneIsFalse = lambda f: lambda cns: False in pmap(f,cns)

allAreTrue = lambda f: lambda cns: False not in pmap(f,cns)
allAreFalse = lambda f: lambda cns: True not in pmap(f,cns)


allcan = lambda fs: lambda cns: False not in map( lambda f:f(cns) ,fs)
conja = lambda fs : lambda x: False not in map(lambda f:f(x),fs)



everyone      = lambda c: agent_pred(c,None,[])
everything    = lambda c: True

# foo = lambda c: "/foo" in c.full_path
# foo3 = lambda c: "/foo3" in c.full_path and foo(c)

# def user(n,g):
#     return lambda c: agent_pred(c,n,g)

user = lambda n,g: lambda c: agent_pred(c,n,g)

# assert that a pred holds over all of the constraints in a constraint set 
# pred : constraint -> bool
# : pred -> constraint set -> bool
can    = oneIsTrue
cannot = allAreFalse
only   = allAreTrue
none   = allAreFalse









def loadGroups(fname):
    #------------------------------------------
    # Open a file which has group lists in the format
    #
    # aaburi01 : other
    # aashok01 : other
    # aberma06 : other grade105
    # aborei01 : other
    #
    #------------------------------------------



    group_str = """blachanc : dip grade105 ta105
chandler : dip grade105 valtweb ta105 valt
kfisher : kfisher grade150pld csfacstaff grade105 csadmin faculty autobahn padsweb ta105 pads fun
jerett : dip grade105 ta105
ywang30 : other grade105 redline autobahn
nr : nr comp50staff faculty ta105 grade105 csfacstaff ghc osbflua bhnr fun ppaml require c--
molay : faculty virtualgrade csfacstaff cssearch grade170 grade111 grade15 ta170 ta10 ta15 grade40 ta40 grade11 ta11 grade160
lfan01 : other grade150nlp ta150nlp
sguyer : faculty csfostud grade181 grade150bugs redline bhnr cssearch abets csfacstaff grade97 abet ta181 nepls heapvis dacapo"""

    group_str = """debugging : debugging"""


    f = open(fname)
    group_str =  f.read().strip()
    f.close()

    closure_users  = defaultdict(lambda :(None,[]))
    closure_groups = defaultdict(lambda: set())

    for l in group_str.split("\n"):
        u,g = [p.strip() for p in l.split(":")]
        grplist = g.split(" ")
        for grp in grplist:
            closure_groups[grp].add(u)
        closure_users[u] = (u,grplist)
    
    #stupid root stuff
    root_grps = closure_groups.keys()

    #disabled to do bug stuff
    # closure_users["root"] = ("root",root_grps)
    # for g in root_grps:
    #     closure_groups[g].add("root")

    return closure_users,closure_groups

closure_users,closure_groups = loadGroups(args.groups)

def closure(g):
    clist = []
    if type(g) != type([]):
    
        for u in closure_groups[g]:
            clist.append(closure_users[u])
        clist.append((None,[g]))
    else:
        users_list = closure_groups[g[0]]
        for grp in g:
            users_list = users_list.intersection(closure_groups[grp])
        
        for u in users_list:
            clist.append(closure_users[u])
        clist.append((None,g))
    
        
    return [user(u,g) for u,g in clist]

# given a username return a user object
def userclosure(uname):
    u,g = closure_users[uname]

    #added this check in case we don't know anything about groups for a user
    if u == None and uname not in ["everyone","anyone"]:
        print("*** Warning: No Group Data for : "+uname +" ***")
        return user(uname,g)
    else:
        return user(u,g)

#given a name, take the closure of that name. 
def mkclosure(n):

    # if type(n) == type(()):
    #     print("this is abstract")
    # if n in closure_users.keys():
    #     return userclosure(n)
    # else:
    #     return disj(closure(n))
    if n in closure_groups.keys() and n in closure_users.keys():
        return userclosure(n)
    else:

        if n in closure_groups.keys():
            return disj(closure(n))
        else:
            return userclosure(n)


cn = mkTree()


def execute_rule(rule,lvl,show_true,show_false,s,show,files):
    r,cantype,perms,agent_set,path_f = rule
    # print("agent_set",agent_set)
    # print("cantype",cantype)
    # print(perms)
    # map the permission from the query into permissions we have precalculated
    
    def xtraf(cn):
        return True
    if perms[0] == "traverse":
        perm_type = "traversable"
    elif perms[0] == "discover":
        perm_type = "discoverable"
    elif perms[0] == "edit":
        perm_type = "editable"
        xtraf = lambda x: x.isFile()
    elif perms[0] == "execute":
        perm_type = "executable"
        xtraf = lambda x: x.isFile()
    else:
        perm_type = "traversable"

    # print(cantype)
    
    #convert ('user':'chandler') to functions
    agent_closure =map(lambda x:mkclosure(x[1]),list(agent_set))


    # user1 \/ user2 ...
    agent_closure_disj = disj(agent_closure)
    
    # bug... gets confused by users and groups with same name

    #can or cannot
    if cantype == "can":
        t_obj_f = can(agent_closure_disj)
        f_obj_f = cannot(agent_closure_disj)
    elif cantype == "canonly":
        t_obj_f = only(agent_closure_disj)
        f_obj_f = none(agent_closure_disj)
    elif cantype == "cannotonly":
        t_obj_f = none(agent_closure_disj)
        f_obj_f = only(agent_closure_disj)
    else:
        t_obj_f = cannot(agent_closure_disj)
        f_obj_f = can(agent_closure_disj)



    # print("stopping before tree build")
    # sys.exit()


    


    l = "x"

    if True:

        accumulator = [0,0]

        def tfun(cn,l,x):
            x[0]= x[0]+ 1

        def ffun(cn,l,x):
            x[1]= x[1] + 1
            
     

        # cn = tree
        # obj_f = objective function (matches users)
        # path_f selects paths to descend
        # tfun = true function based on obj_f output
        # ffun = false function based on obj_f output

        trueF  = lambda cn,l:tfun(cn,l,accumulator)
        falseF = lambda cn,l:ffun(cn,l,accumulator)


        #correct path function

      

        # cn     = root of tree
        # obj_f  = user function
        # path_f = path function
        # trueF  = function to call if true
        # falseF = function to call if false

        # print("-")*80        
        # print("Query Results for: ")
        # print(str(s))
        # print("")
        # print("-")*80
        #tup = querytf(cn,can(allOf(mkclosure("chandler"),mkclosure("kfisher"))),"*"+l+"*",path_f,trueF,falseF,)

        # ff = disj([cannot(mkclosure("jchandler"))])
        # tf = conj([can(mkclosure("sguyer")),ff])
        tup = querytf(cn,t_obj_f,perm_type,"*"+l+"*",path_f,trueF,falseF,lvl,show_true,show_false,xtraf,show,files)
        a1,b1,childname,k,rows = tup
        print("-"*80)

        if rows == []:
            print("No instances could be found which satisfy your query")
        else:
            #print("(      1 ,      3 )")
            print("(   True ,  False )")
        for r,xr in rows:
            print(r)
            if show:
                if xr == []:
                    print("")
                    print("\t Empty Constraint Set: Action Impossible" )
                    print("")
                else:
                    print("")
                    for x in xr:
                        print(x)
                    print("")
        # print("-")*80
        # #tup = querytf(cn,can(allOf(mkclosure("chandler"),mkclosure("kfisher"))),"*"+l+"*",path_f,trueF,falseF,)

        # ff = disj([cannot(mkclosure("kfisher"))])
        # tf = conj([can(mkclosure("sguyer")),ff])
        # tup = querytf(cn,tf,"*"+l+"*",path_f,trueF,falseF,4)


        # print("-")*80
        # #tup = querytf(cn,can(allOf(mkclosure("chandler"),mkclosure("kfisher"))),"*"+l+"*",path_f,trueF,falseF,)

        # ff = disj([cannot(mkclosure("jchandler")),cannot(mkclosure("kfisher"))])
        # tf = conj([can(mkclosure("sguyer")),ff])
        # tup = querytf(cn,tf,"*"+l+"*",path_f,trueF,falseF,4)


        # print("-")*80
        # #tup = querytf(cn,can(allOf(mkclosure("chandler"),mkclosure("kfisher"))),"*"+l+"*",path_f,trueF,falseF,)

        # tf = conj([can(mkclosure("sguyer")),cannot(mkclosure("jchandler")),cannot(mkclosure("kfisher"))])
        # tup = querytf(cn,tf,"*"+l+"*",path_f,trueF,falseF,4)





def run(s,l,show_true,show_false,show,files):
    print("="*80)
    #print("*"*40)
  
    #print("Command:")
    #print("*"*40)
    print("Command: " + s)
    #print("*"*40)
    #print("")
        

    for r in parse(s):
        #print('showing:',show)
        execute_rule(r,l,show_true,show_false,s,show,files)

    print("-"*80)
    print("")

rootpathcmd = "path base = "+  cn.path + "/.*"
rootownercmd = "agent owner = "+  cn.user

# run(rootpathcmd,3,True,True,False,False)
# run(rootownercmd,3,True,True,False,False)

rte = []

#global args
if args.rules:
    f = open(args.rules)
    data = f.read().strip()
    f.close()
    xs = data

    statements = [ys.strip() for ys in xs.split(";")]
    if statements[-1] == "":
        statements = statements[:-1]

    for statement in statements:
        run(statement,5,True,True,False,False)

        # rte = parse(s)

        # for r in rte:
        #     print("r in rte",r)

        # # 
        # print("rte",rte)



        # for rule in rte:
        #     #execute_rule(rule,10,True,False,"")



from cmd import Cmd

class MyPrompt(Cmd):


    def do_query(self, args):
        """Runs a query"""
        # if len(args) == 0:
        #     name = 'stranger'
        # else:
        #     name = args
        #print "Hello, %s" % name
        run(args,self.default_depth,True,True,self.show,self.files)

    def do_counterexample(self,args):
        """Shows a counterexample for a query"""
        run(args,self.default_depth,False,True,self.show,self.files)

    def do_example(self,args):
        """Shows examples for a  query"""
        run(args,self.default_depth,True,False,self.show,self.files)

    def do_files(self,args):
        """Sets and displays xray mode: xray [on|off]"""
        if len(args) > 0:
            if args == "on":
                self.files = True
                #self.prompt = str(self.default_depth) +' >>> '
            else:
                self.files = False
                #self.prompt = str(self.default_depth) +' > '
            #self.show = int("".join(args))
        if self.files:
           
            print("Files is ON")

        else:
            print("Files is OFF")

    def do_xray(self,args):
        """Sets and displays xray mode: xray [on|off]"""
        if len(args) > 0:
            if args == "on":
                self.show = True
                self.prompt = str(self.default_depth) +' >>> '
            else:
                self.show = False
                self.prompt = str(self.default_depth) +' > '
            #self.show = int("".join(args))
        if self.show:
           
            print("XRAY is ON")

        else:
            print("XRAY is OFF")  
    def do_env(self,args):
        """Displays the contents of the environment"""
        dprintenv(env)

    def do_depth(self,args):
        """Sets and displays depth: depth [on|off]"""
        if len(args) > 0:
            self.default_depth = int("".join(args))
            self.prompt = str(self.default_depth) +' > '
        print("Depth is %s" % self.default_depth )      

    def do_quit(self, args):
        """Quits the program."""
        print("Quitting.")
        raise SystemExit

    def do_banner(self,args):
        """Prints Banner"""
        print(self.banner)
    def default(self,args):
        print(args)
        run(args,self.default_depth,True,True,self.show,self.files)
def debug():
    global args
    from collections import defaultdict

    up = defaultdict(lambda:0)

    fc = open(args.fname+"_counts","w")
    def countCons(cn):
        depth = cn.depth
        #print(cn.rec["raw"])
        for label in sorted(cn.configurations_sets.keys()):
            c = cn.getConf(label)
            if c == None:
                c = []
            #for cc in c:
            #    print("\t"+label+str(cc))
            for cc in c:
                up[str(cc)]+=1
            fc.write(label+"\t"+str(depth)+"\t"+str(len(c))+"\n")
        if cn.getChildren()!=[]:
            for c in cn.getChildren():
                countCons(c)

    countCons(cn)

    print("lenup",len(up.keys()))
    for i in up.keys():
        print(i,up[i])

    fc.close()
if __name__ == '__main__':
    
    prompt = MyPrompt()
    prompt.banner = """
===================================================================
 __   _______       __     __
 \ \ / /  __ \     /\\ \   / /   File Permission Query Environment 
  \ V /| |__) |   /  \\ \_/ /   
   > < |  _  /   / /\ \\   /     File:   %s
  / . \| | \ \  / ____ \| |     Groups: %s
 /_/ \_\_|  \_\/_/    \_\_|     Root:   %s 

===================================================================""" % (args.fname,args.groups,cn.path)
    prompt.default_depth = 4
    prompt.show = False
    prompt.files = False
    prompt.prompt = str(prompt.default_depth) +' > '
    #prompt.do_banner("")
    prompt.cmdloop(prompt.banner)



