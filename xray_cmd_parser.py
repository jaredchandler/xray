import pyparsing as pp
import Agents
import argparse


from settings import *

import re
global args
agent = Agents.Agent(args.groups)
#===========================

def printenv(e):
    # print("")
    # print("========ENVIRONMENT=======")
    # for k in e.keys():
    #     print("\t"+k)
    #     print("\t\t"+str(e[k]))
    # print("--------------------------")
    # print("")
    pass

def dprintenv(e):
    print("")
    print("========ENVIRONMENT=======")
    for k in e.keys():
        print("\t"+k.replace("_"," "))
        print("\t\t"+str(e[k]))
    print("--------------------------")
    print("")
    pass

env = {}

def env_set(id,v):
    env[id] = v
    return env[id]

def env_get(id):
    return env[id]

def parse(s):
    orig_s = s

    rules_to_execute = []

    def mk_agent_set(s):
        return ('agent',s)

    #given a regex and a input return true or false if regex accepts input
    def mkroot(regex,y):
        if re.compile("^"+regex+"$",flags=re.DOTALL).match(y) != None:
            return True
        else:
            return False

        #return x == y


    assert(mkroot("abc","abc")==True)
    assert(mkroot("abc","abcd")==False)
    assert(mkroot("abc.*","abcd")==True)
    assert(mkroot("abc","ab")==False)
    assert(mkroot("/g/comp/105/.*","/g/comp/105/")==True)
    assert(mkroot("/g/comp/105/.*","/g/comp/160/")==False)



    #given a path object, return path function: string -> boolean
    def mkf(x):
        path = x["path"][0]
        return lambda y: mkroot(path,y)

    assert(mkf({'path':['abc']})('abc')==True)
    assert(mkf({'path':['abc']})('abcd')==False)
    assert(mkf({'path':['abc']})('ab')==False)
    assert( mkf({'path':["/g/comp/105/.*"]})("/g/comp/105/foo") == True )


    #given a list of path objects return a list of path functions
    def mkchain(xs):
        if type(xs) != type([]):
            xs = [xs]
        fs = map(mkf,xs)
        return fs


    #given a list of path objects return a disjunctive path function
    # list(paths) -> function: string -> bool
    def mk(xs):
        fs = mkchain(xs)
        return lambda path:True in map(lambda g:g(path),fs)

    assert(mk([{'path':['abc']}])("abc")==True)
    assert(mk([{'path':['abc']}])("abcd")==False)
    assert(mk([{'path':['abc']},{'path':['abcd']}])("abcd")==True)



    #given a pair of functions (a,b), return a function which returns true if either (a or b) returns true
    def mk_or(a,b):
        #or two functions
        def f_or(x,a,b):
            if a(x):
                return True
            else:
                return b(x)
        return lambda y: f_or(y,a,b)

    #given a pair of functions (a,b), return a function which returns true if both (a and b) return true
    def mk_and(a,b):
        #and two functions
        def f_and(x,a,b):
            if a(x):
                return b(x)
            else:
                return False
        return lambda y: f_and(y,a,b)

    #given a fragment of the AST, return a function. 
    def path2function(r):
        #print("rec",r)
        if "pathset" in r:
            v= r["pathset"][0]
            #print(v)
            return mk(v)
        elif "pathvar" in r:
            key = r["pathvar"][0]
            #print("key",key,env[key])
            v = env[key]
            return v
        elif "agentvar" in r:
            #print("path2function, agentvar",r)
            #key = r["agentvar"][0]
            key = r["agentvar"]

            #print("key",key,env["agent_"+key])
            v = env["agent_"+key]
            return v
        elif "agentset" in r:
            #print("path2function agentset",r)
            #v= r["agentset"][0]
            v = r["agentset"]
            #print("agentset..",v)
            return v
        elif "agentapplication" in r:
            a = r["agentapplication"]
            lhs = a[0]["lhs"][0]
            v1 = path2function(lhs)
            #print("LHS of agent application",lhs,path2function(lhs))
            #case where we just have a single operand and parens
            if len(a)==1:
                return v1 #in this case just get the value
            rhs = a[2]["rhs"][0]
            #print("RHS of agent application",rhs,path2function(rhs))
            op  = a[1]["op"][0]
            v2 = path2function(rhs)

            if op == "or":
                return v1.union(v2)
            elif op == "and":
                return v1.intersection(v2)
            elif op == "minus":
                return v1.difference(v2)
            else:
                return lambda x:None

            print("error")
            1 / 0
        else:
            if "application" in r:
                a = r["application"]
                lhs = a[0]["lhs"][0]
                v1 = path2function(lhs)

                #case where we just have a single operand and parens
                if len(a)==1:
                    return v1
                
                rhs = a[2]["rhs"][0]
                op  = a[1]["op"][0]

                v2 = path2function(rhs)
                
                if op == "or":
                    return mk_or(v1,v2)
                elif op == "and":
                    return mk_and(v1,v2)
                elif op == "minus":
                    return mk_and(v1,lambda x: not v2(x))
                else:
                    return lambda x:None
            else:
                return lambda x:None


    def agent2f (n):
        #print("making " + str(n) + " into a f")
        #return n
        return "making " + str(n) + " into a f"

    #===========================

    def parseToDict(x,lbl):
        r = x.asList()
        return {lbl:r}

    def f(lbl):
        return lambda x: parseToDict(x,lbl) 

    def fprim(lbl):
        return lambda x: {lbl:x.asList()[0]} 

    PATH = pp.Word(pp.alphanums+"+-./*?")("PATH")
    PATH.setParseAction(f("path"))

    LP      = pp.Literal("(")("LP")
    RP      = pp.Literal(")")("RP")
    LBRACE  = pp.Word("{")("{")
    RBRACE  = pp.Word("}")("}")
    LBRACK  = pp.Word("[")("[")
    RBRACK  = pp.Word("]")("]")
    EQ      = pp.Word("=")


    OPS     = pp.Word("and") | pp.Word("or") | pp.Word("minus") 
    OP      = OPS("OP")
    OP.setParseAction(f("op"))

    PATHBODY    = pp.delimitedList(PATH,delim=',')("PATHS")
    PATHBODY.setParseAction(lambda s,l,t:t)

    PATHOPTION  = pp.Group(pp.Suppress(LBRACE)+PATHBODY+pp.Suppress(RBRACE))
    PATHOPTION.setParseAction(lambda s,l,t:t[0])

    PATHSET     = pp.Group(pp.Or([PATHOPTION,PATH]))
    #PATHSET.setParseAction(lambda x:x.asList())
    PATHSET.setParseAction(f("pathset"))


    GROUP = pp.Suppress(pp.Word("users")) + pp.Suppress(pp.Word("in")) + pp.Word(pp.alphanums)#.setResultsName("GROUP")

    GROUP.setParseAction(lambda x:('group',x.asList()[0]))


    ABSTRACT = pp.Suppress(LBRACK) + pp.Word(pp.alphanums)("absuser") + pp.Suppress(pp.Word(",")) +  pp.Optional(pp.Word(pp.alphanums+","))("absgroups")+ pp.Suppress(RBRACK)
    ABSTRACT.setParseAction(lambda x:('abstract',x.asDict()))


    USER = pp.NotAny(pp.Keyword("agent")) + pp.Word(pp.alphanums)

    USER.setParseAction(lambda x:('user',x.asList()[0]))


    AGENT =     pp.Group(pp.Or([USER,GROUP]))

    AGENT.setParseAction(lambda x:x.asList()[0])
    



    AGENTBODY    = pp.delimitedList(AGENT,delim=',')("AGENTS")
    AGENTBODY.setParseAction(lambda s,l,t:t)

    AGENTOPTION  = pp.Group(pp.Suppress(LBRACE)+AGENTBODY+pp.Suppress(RBRACE))
    AGENTOPTION.setParseAction(lambda s,l,t:t[0])

    AGENTSET     = pp.Group(pp.Or([AGENTOPTION,AGENT]))

    AGENTSET.setParseAction(lambda x:{"agentset":set(agentset2set(x.asList()[0]))})

    def agentset2set(xs):
        base = []
        for x in xs:
            if x[0] == 'user':
                 base.append(x)
            else:
                 base = base + agent.mkGroup(x[1])

        return base 




    IDENTIFIER = pp.Word(pp.alphanums)("ID")

    # agentexp

    AGENTEXP = pp.Forward()


    # -- should change AGENTEXP to AGENTATOM
    AGENTATOMPAIR = pp.Suppress(LP) + AGENTEXP + pp.Suppress(RP)
    AGENTATOMPAIR.setParseAction(f("agentapplication"))

    #used for creating vars and dereferencing vars

    AGENTVAR = pp.Suppress(pp.Word("agent")) + IDENTIFIER
    #AGENTVAR.setParseAction(f("agentvar"))
    AGENTVAR.setParseAction(lambda x:{"agentvar":x.asList()[0]})


    AGENTATOM = AGENTATOMPAIR  | AGENTSET | AGENTVAR  

    AGENTATOML = AGENTATOM("LEFT")
    AGENTATOML.setParseAction(f("lhs"))

    AGENTATOMR = AGENTATOM("RIGHT")
    AGENTATOMR.setParseAction(f("rhs"))
    AGENTEXP  << AGENTATOML + pp.Optional(OP + AGENTATOMR)


    AGENTASSIGNMENT =  AGENTVAR + pp.Suppress(EQ) + AGENTATOM
    AGENTASSIGNMENT.setParseAction(f("agentassignment"))


    # pathexp
    PATHEXP = pp.Forward()

    PATHATOMPAIR = pp.Suppress(LP) + PATHEXP + pp.Suppress(RP)
    PATHATOMPAIR.setParseAction(f("application"))

    #used for creating vars and dereferencing vars

    PATHVAR = pp.Suppress(pp.Word("path")) + IDENTIFIER
    PATHVAR.setParseAction(f("pathvar"))


    PATHATOM = PATHATOMPAIR | PATHVAR | PATHSET 

    PATHATOML = PATHATOM("LEFT")
    PATHATOML.setParseAction(f("lhs"))

    PATHATOMR = PATHATOM("RIGHT")
    PATHATOMR.setParseAction(f("rhs"))
    PATHEXP  << PATHATOML + pp.Optional(OP + PATHATOMR)


    PATHASSIGNMENT =  PATHVAR + pp.Suppress(EQ) + PATHATOM
    PATHASSIGNMENT.setParseAction(f("pathassignment"))


    CAN = pp.Word("cannot") | pp.Word("can") 
    CAN.setParseAction(f("bool"))

    READ =      pp.Word("read")
    WRITE =     pp.Word("write")
    EXECUTE =   pp.Word("execute")
    TRAVERSE =  pp.Word("traverse")
    DISCOVER =  pp.Word("discover")
    EDIT =  pp.Word("edit")
    PERMISSION =pp.Word("permission")

    PERMS =     pp.Or([READ,WRITE,EXECUTE,TRAVERSE,PERMISSION,EXECUTE,DISCOVER,EDIT])
    AND =       pp.Word("and")
    PERMLIST = pp.delimitedList(PERMS,delim=AND).setResultsName("PERMS")
    PERMLIST.setParseAction(lambda x:x.asDict())

    # RULEATOM = ATOM
    # RULEATOM.setParseAction(lambda x:path2function(x))
    #ONLY = pp.Optional(pp.Word("only"))("ONLY")


    RULE =  AGENTATOM + CAN + PERMLIST + pp.Word("in") + PATHATOM
    RULE.setParseAction(f("rule"))

    ONLYRULE =  pp.Suppress(pp.Word("only")) + AGENTATOM + CAN + PERMLIST + pp.Word("in") + PATHATOM
    ONLYRULE.setParseAction(f("onlyrule"))

    COMMENT = pp.Suppress(pp.Word("#") + pp.Word(pp.alphanums+"+-./*? "))
    ATOMS = pp.ZeroOrMore(AGENTASSIGNMENT + pp.Optional(COMMENT) 
        | PATHASSIGNMENT + pp.Optional(COMMENT) 
        | ONLYRULE + pp.Optional(COMMENT) 
        | RULE + pp.Optional(COMMENT)
        | PATHATOM + pp.Optional(COMMENT) 
        | COMMENT)  




    def parseStatement(statement):
        #print("parseStatement asked to parse",str(statement))
        if "pathassignment" in statement:
            s = statement["pathassignment"]

            #get the id to which the result is to be assiged
            id = s[0]["pathvar"][0]
            v = path2function(s[1])
            env_set(id,v)
            printenv(env)
            return s
        elif "agentassignment" in statement:
            s = statement["agentassignment"]

            #get the id to which the result is to be assiged
            id = s[0]["agentvar"][0]
            id = s[0]["agentvar"]
            

            #print("...agentassignment",s[1])
            v = path2function(s[1])
            #v= s[1]
            env_set("agent_"+id,v)
            #used to show state of environment
            printenv(env)
            return s
        elif "onlyrule" in statement:
            #print("this is a rule")
            s = statement["onlyrule"]
            #print("s**",s)
            #print("rule agent", s[0])
            agent = path2function(s[0])
            #print("the agent is: " + str(agent))
            #print("agentinvoke",agent(1))
            s[0] = agent
            cantype = s[1]['bool'][0] + "only"
            s[1]["only"] = True
            #print(cantype)
            perms = s[2]['PERMS']
            path = s[4]
            #print(s[4])
            f= path2function(s[4])

            #print("the path '" +str(s[4])+ "'' is represented by a function: " + str(f) )
            s[4] = f
            #print(f)
            #print(s)
            #printenv(env)
            rules_to_execute.append((s,cantype,perms,agent,f))


            return s

        elif "rule" in statement:
            #print("this is a rule")
            s = statement["rule"]
            #print("s**",s)
            #print("rule agent", s[0])
            agent = path2function(s[0])
            #print("the agent is: " + str(agent))
            #print("agentinvoke",agent(1))
            s[0] = agent
            cantype = s[1]['bool'][0]
            #print(cantype)
            perms = s[2]['PERMS']
            path = s[4]
            #print(s[4])
            f= path2function(s[4])

            s[4] = f
            #print(f)
            #print(s)
            #printenv(env)
            rules_to_execute.append((s,cantype,perms,agent,f))
            return s

    #print(AGENTATOM.parseString(s.strip()))
    print("="*80)
    statements = ATOMS.parseString(s.strip())
    
    for statement in statements:
        
        r= parseStatement(statement)

        
    #debugging stuff
    # print("-->user",USER.parseString("user1")[0])
    # print("--->group", GROUP.parseString("users in comp105")[0])
    # print("--->agent",AGENT.parseString("users in comp105")[0])
    # print("--->agent",AGENT.parseString("users1")[0])
    # print("--->agentset",AGENTSET.parseString("{user1,user2,users in comp105}")[0])
    # print("--->agentvar",AGENTVAR.parseString("agent xyz")[0])
    # print("--->agentOP",AGENTATOMPAIR.parseString("(agent xyz and {user1,users in groupxxx,user3})")[0])


    return rules_to_execute




