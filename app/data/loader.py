import pandas as pd
import numpy as np
import os


def read_data(file_path):

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".xlsx":
        df = pd.read_excel(file_path, header=None)

    elif ext == ".csv":
        df = pd.read_csv(file_path, header=None)

    else:
        raise ValueError("Unsupported file format")

    vertices_number = int(df.iloc[0, 1])
    vertices = df.iloc[2, 1: 1 + vertices_number].tolist()

    subset_size = int(df.iloc[1, 3])

    quotas = df.iloc[1, 5: 5 + vertices_number].to_numpy(dtype=np.float64)

    row_start = 3
    row_end = row_start + vertices_number
    col_start = 1
    col_end = col_start + vertices_number

    matrix = df.iloc[row_start:row_end, col_start:col_end].to_numpy(dtype=np.float64)
    matrix = np.nan_to_num(matrix, nan=0)

    return vertices, subset_size, quotas, matrix

def check_file(file_path):
    pass