# This code is for the project of "converged inter/intra datacenter networks".
# This core maintains network states and responds to setup/teardown requests.

__author__ = "Ke Wen"
__copyright__ = "Copyright 2015, Lightwave Research Laboratory, Columbia University"
__email__ = "kw2501@columbia.edu"

from rwa import *

graph_ = {}         # dic: node->neighbor list (see rwa.test())
resource_ = {}      # dic: edge->lambda list (edge format: u + "->" + v)
nlambda_ = 0        # number of lambda per link
connTable_ = {}     # dic: cid->assignment

def init(graph, nlambda):
    #print ("init")
    global graph_
    global nlambda_
    global resource_
    graph_ = graph
    nlambda_ = nlambda
    for u in graph_:
        for v in graph_[u]:
            edge = u + "->" + v
            resource_[edge] = list(range(nlambda_))

def request_conn(cid, src, dst):
    #print ("request_conn", cid, src, dst)
    global connTable_
    assignment = find_assignment(graph_, resource_, nlambda_, src, dst)
    if assignment != ():
        update_resource(assignment, "+")
        connTable_[cid] = assignment
    return assignment


def update_resource(assignment, op):
    #print ("update_resource")
    global resource_
    path = assignment[0]
    w = assignment[1]
    edges = []
    for i in range(len(path)-1):
        j = i + 1
        edges.append(path[i] + "->" + path[j])
    if op == "+":
        for e in edges:
            resource_[e].remove(w)
    elif op == "-":
        for e in edges:
            resource_[e].append(w)
    else:
        print("Wrong Update Operation Code!")


def clean_conn(cid):
    #print ("clean_conn")
    global connTable_
    if cid not in connTable_:
        print("No Connection Found!")
    else:
        update_resource(connTable_[cid], "-")
        del connTable_[cid]

def path_wav_compute(channel_id, topo, nlambda, src, dst):
    #print ("path wav compute")
    graph = topo
    init(graph, nlambda)
    paths=[]
    for i in range(3):          
        paths.append(request_conn(channel_id, src, dst))
    return paths

def rwa_core_test2():
    graph = {'A':['B', 'C'], 'B':['A', 'C'], 'C':['A','B']}
    nlambda = 3
    init(graph, nlambda)
    paths=[]
    '''
    print request_conn('c1','A','B')
    print request_conn('c2','B','A')        # Notice that the result assumes a new wavelength for every connection, even if it's the same two nodes but reversed!
    print request_conn('c3','A','D') 
    print request_conn('c4','A','E')
    print request_conn('c5','A','B')
    '''
    for i in range(3):
        paths.append(request_conn('c1','A','B'))
    print (paths)

#rwa_core_test2()
