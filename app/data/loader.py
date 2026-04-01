import pandas as pd
import numpy as np
import os
import networkx as nx

def read_data(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    df = pd.DataFrame()
    vertices = []
    subset_size = 0
    quotas = {}
    graph = nx.DiGraph()

    if ext == ".xlsx":
        df, vertices, subset_size, quotas, graph = parse_xlsx(file_path)
    elif ext == ".csv":
        pass
    else:
        raise ValueError("Unsupported file format")

    return df, vertices, subset_size, quotas, graph

def parse_xlsx(file_path):
    df = pd.read_excel(file_path, header=None)

    vertices_number = int(df.iloc[0, 1])

    vertices = df.iloc[2, 1: 1 + vertices_number].tolist()

    subset_size = int(df.iloc[1, 3])

    quotas = df.iloc[1, 5: 5 + vertices_number].to_numpy(dtype=np.float64)

    q = {}
    for i in range(vertices_number):
        q[vertices[i]] = quotas[i]

    row_start = 3
    row_end = row_start + vertices_number
    col_start = 1
    col_end = col_start + vertices_number
    matrix = df.iloc[row_start:row_end, col_start:col_end].to_numpy(dtype=np.float64)
    matrix = np.nan_to_num(matrix, nan=0)
    graph = nx.DiGraph()

    for i in range(vertices_number):
        graph.add_node(vertices[i], quota=quotas[i])

    for i in range(vertices_number):
        for j in range(vertices_number):
            weight = matrix[i][j]
            if weight != 0:
                graph.add_edge(vertices[i], vertices[j], weight=weight)

    return df, vertices, subset_size, q, graph