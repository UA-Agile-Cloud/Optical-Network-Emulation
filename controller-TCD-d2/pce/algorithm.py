
class Algorithm():
    
    def __init__(self):
        self.index = 0
    
    def get_min_index(self, distances):
        return distances.index(min(distances))
        
    def linear_path(self, node_no, tx_node, rx_node, adjacency_matrix):
        distances = []
        indexes = []
        i = tx_node-1
        j = 0
        dst = rx_node-1
        sequence = []
        while True:
            while j < node_no:
                distance = adjacency_matrix[i][j]
                if distance is not 0:
                    indexes.append(j)
                    distances.append(distance)
                j += 1
                    
            min_node_index = self.get_min_index(distances)
            node = indexes[min_node_index]
            sequence.append([i+1, node+1])
            
            if node == dst:
                break
            
            i = node
            j=0
            distances = []
            indexes = []
            
        return sequence

    def ConstructPath(self, path, p, i, j):
        self.index += 1
        i,j = int(i), int(j)            
        if(i==j):
            path.append(i)
            return path
        elif(p[i][j] == -30000):
            return None
        else:
            path.append(j)
            self.ConstructPath(path, p, i, p[i][j]);
            return path

    def build_sequence(self, path):
        sequence = []
        for i in range(len(path)-1):
            sequence.append([path[i]+1, path[i+1]+1])
        return sequence

    def floyd_warshall_shortest_path(self, node_no, tx_node, rx_node, adjacency_matrix):
        path_matrix = [[0 for column in range(node_no)] 
                                        for row in range(node_no)]
        for i in range(0,node_no):
            for j in range(0,node_no):
                path_matrix[i][j] = i
                if (i != j and adjacency_matrix[i][j] == 0): 
                    path_matrix[i][j] = -30000 
                    adjacency_matrix[i][j] = 30000
        
        for k in range(0,node_no):
            for i in range(0,node_no):
                for j in range(0,node_no):
                    if adjacency_matrix[i][j] > adjacency_matrix[i][k] + adjacency_matrix[k][j]:
                        adjacency_matrix[i][j] = adjacency_matrix[i][k] + adjacency_matrix[k][j]
                        path_matrix[i][j] = path_matrix[k][j]

        path = []
        path = self.ConstructPath(path, path_matrix,tx_node-1,rx_node-1)
        if path is not None:
            return self.build_sequence(path[::-1])
        return 0
