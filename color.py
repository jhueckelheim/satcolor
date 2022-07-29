#!/usr/bin/env python 

import sys
import numpy as np
import z3

if(len(sys.argv) < 2):
    print("Usage: ", sys.argv[0], " <sparsity_file>")

def file_to_adj_matrix(filename):
    """
    Read matrix from file into numpy boolean array.
    Example:
    10
    01
    will become: [[True,False],[False,True]]
    All non-digit characters are ignored, 0 is interpreted as False,
    other digits are interpreted as True.
    """
    with open(filename) as fp:
        adj_list = [[num!="0" for num in line if num.isdigit()] for line in fp]
    return np.matrix(adj_list, dtype=bool)

def is_col_intersecting(matrix, colidx1, colidx2):
    """
    Test if two columns in matrix have any intersection, i.e. have non-zeros
    in the same row.
    """
    col1 = matrix[:,colidx1]
    col2 = matrix[:,colidx2]
    return np.any(np.logical_and(col1, col2))

def is_row_intersecting(matrix, rowidx1, rowidx2):
    """
    Test if two rows in matrix have any intersection, i.e. have non-zeros
    in the same column.
    """
    return is_col_intersecting(matrix.transpose(), rowidx1, rowidx2)

def find_coloring(matrix, n_colors):
    """
    Attempt to color the matrix with the given number of colors
    The approach is taken from https://www.cs.cmu.edu/~15414/lectures/15-sat-encodings/z3_demo.html
    """
    n_rows, n_cols = adj_matrix.shape
    
    nodes = ["n%d"%i for i in range(n_cols)]
    edges = []
    for colidx1 in range(n_cols):
        for colidx2 in range(colidx1+1, n_cols):
            if(is_col_intersecting(adj_matrix, colidx1, colidx2)):
                edges.append(("n%d"%colidx1, "n%d"%colidx2))
    colors = ["c%d"%i for i in range(n_colors)]
    
    vs = []
    for node in nodes:
        for color in colors:
            vs.append(z3.Bool('%s%s'%(node, color)))

    adjacent_not_same = []
    for (n1, n2) in edges:
        for color in colors:
            v1 = z3.Bool('%s%s'%(n1, color))
            v2 = z3.Bool('%s%s'%(n2, color))
            adjacent_not_same.append(z3.Or(z3.Not(v1), z3.Not(v2)))

    at_least_one_color = []
    for node in nodes:
        disj = []
        for color in colors:
            disj.append(z3.Bool('{}{}'.format(node, color)))
        at_least_one_color.append(z3.Or(disj))

    at_most_one_color = []
    for node in nodes:
        for i in range(len(colors)):
            for j in range(i+1, len(colors)):
                at_most_one_color.append(z3.Or([z3.Not(z3.Bool('%s%s'%(node, colors[i]))), 
                                            z3.Not(z3.Bool('%s%s'%(node, colors[j])))]))

    s = z3.Solver()
    s.add(adjacent_not_same)
    s.add(at_least_one_color)
    s.add(at_most_one_color)
    if s.check() == z3.sat:
        for v in nodes:
            for color in colors:
                if z3.is_true(s.model().eval(z3.Bool('%s%s'%(v, color)))):
                    print("node %s has color %s"%(v, color))
        return True
    else:
        return False

adj_matrix = file_to_adj_matrix(sys.argv[1])
i = 0
while True:
    i = i+1
    print("attempting with %d colors"%i)
    if find_coloring(adj_matrix, i):
        break
