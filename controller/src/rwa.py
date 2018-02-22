#!/usr/bin/env python
# This code is for the project of "converged inter/intra datacenter networks".
# This code provides functions needed in a general dynamic wavelength routing and assignment problem.

__author__ = "Ke Wen"
__copyright__ = "Copyright 2015, Lightwave Research Laboratory, Columbia University"
__email__ = "kw2501@columbia.edu"

def find_all_paths(graph, start, end, path=[]):
    #print ("find all paths")
    path = path + [start]
    if start == end:
        return [path]
    #if not graph.has_key(start):
    if not start in graph:
        return []
    paths = []
    for node in graph[start]:
        if node not in path:
            newpaths = find_all_paths(graph, node, end, path)
            for newpath in newpaths:
                paths.append(newpath)
    paths.sort(key=lambda p: len(p))
    return paths

def find_shortest_path(graph, start, end, path=[]):
    #print ("find shortest path")
    path = path + [start]
    if start == end:
        return path
    #if not graph.has_key(start):
    if not start in graph:
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest

def find_wavelength(path, res, nlambda):
    #print ("find wavelength")
    edges = []
    for i in range(len(path)-1):
        j = i + 1
        edges.append(path[i] + "->" + path[j])
    for w in range(nlambda):
        avail = True
        for e in edges:
            if w not in res[e]:
                avail = False
                break
        if not avail:
            continue
        else:
            return w
    return -1

def find_assignment(graph, res, nlambda, u, v):
    #print ("find assignment")
    paths = find_all_paths(graph, u, v)
    w = -1
    for path in paths:
        w = find_wavelength(path, res, nlambda)
        if w < 0:
            continue
        else:
            break
    if w < 0:
        return ()
    else:
        return (path, w)
'''
def rwa_test():
    graph = {'A': ['B'],
             'B': ['C', 'D'],
             'C': ['D'],
             'D': ['C'],
             'E': ['F'],
             'F': ['C']}

    nlambda = 100
    for u in graph:
        for v in graph[u]:
            edge = u + "->" + v
            resource[edge] = range(nlambda)

    print find_assignment(graph, resource, nlambda, 'A', 'D')
'''
