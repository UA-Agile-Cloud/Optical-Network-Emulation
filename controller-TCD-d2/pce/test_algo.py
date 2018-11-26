import algorithm
al = algorithm.Algorithm()
matrix = [[0,1,0,0, 0],[0,0,1,0, 0],[0,0,0,1, 0], [0,0,0,0, 1], [0,0,0,0, 0]]
al.floyd_warshall_shortest_path(5,4,5,matrix)

