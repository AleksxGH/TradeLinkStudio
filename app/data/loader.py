import pandas as pd
import numpy as np
import os
import csv
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
        df, vertices, subset_size, quotas, graph = parse_csv(file_path)
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


def parse_csv(file_path):
    """
    Parse CSV in format:
        v1, v2, v3, quota
        v1, w11, w12, w13, q1
        v2, w21, w22, w23, q2
        v3, w31, w32, w33, q3
    
    Where:
    - First row: vertex names starting from column 0, ending with "quota"
    - Data rows: vertex_name, weights..., quota_value
    - Matrix must be square (n vertices = n data rows)
    - Each data row must have n+2 elements (name, n weights, quota)
    - Empty cells inside the matrix are treated as 0
    
    Returns (df, vertices, subset_size, quotas_dict, graph)
    """
    def _read_text_with_fallback_encodings(path):
        for encoding in ('utf-8', 'latin-1', 'utf-16'):
            try:
                with open(path, 'r', encoding=encoding) as file_handle:
                    return file_handle.read()
            except Exception:
                continue
        raise ValueError("Unable to read CSV file with supported encodings")

    def _parse_number(raw_value, row_idx, col_idx, field_name):
        value = raw_value.strip()
        if value == "":
            return 0.0

        value = value.replace(' ', '').replace(',', '.')

        try:
            return float(value)
        except ValueError:
            raise ValueError(
                f"Row {row_idx}, column {col_idx}: invalid {field_name} value '{raw_value}'"
            )

    raw_text = _read_text_with_fallback_encodings(file_path)
    raw_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    if not raw_lines:
        raise ValueError("CSV file is empty or has too few rows")

    normalized_lines = []
    for line in raw_lines:
        if len(line) >= 2 and line[0] == '"' and line[-1] == '"':
            line = line[1:-1]
        normalized_lines.append(line)

    sample_text = '\n'.join(normalized_lines[:5])
    delimiter = ';' if sample_text.count(';') >= sample_text.count(',') else ','
    rows = list(csv.reader(normalized_lines, delimiter=delimiter))

    if not rows or len(rows) < 2:
        raise ValueError("CSV file is empty or has too few rows")

    # Extract header: first row contains vertex names and "quota" label
    header_row = [cell.strip() for cell in rows[0]]
    vertex_names = []
    
    # Find "quota" column index
    quota_col_idx = None
    for i, val in enumerate(header_row):
        if val.lower() == "quota":
            quota_col_idx = i
            break
    
    if quota_col_idx is None:
        raise ValueError("CSV header must contain 'quota' label")
    
    # Extract vertex names (all columns before "quota")
    vertex_names = [header_row[i].strip() for i in range(quota_col_idx) if header_row[i].strip()]
    
    if not vertex_names:
        raise ValueError("No vertices found in CSV header")

    n = len(vertex_names)
    
    # Parse data rows
    matrix_data = []
    quotas_list = []

    for row_idx in range(1, len(rows)):
        row = [cell.strip() for cell in rows[row_idx]]
        
        # Skip empty rows
        if not row or all(not cell for cell in row):
            continue

        # Support both formats:
        # - name + n weights + quota
        # - blank leading cell + n weights + quota
        # - n weights + quota
        if len(row) == n + 2:
            weight_start = 1
        elif len(row) == n + 1:
            weight_start = 0
        else:
            raise ValueError(
                f"Row {row_idx} has {len(row)} elements, expected {n + 2} "
                f"or {n + 1} elements depending on whether a row label is present"
            )

        # Extract weights
        weights = []
        for j in range(n):
            source_index = weight_start + j
            try:
                weights.append(_parse_number(row[source_index], row_idx, source_index, "weight"))
            except IndexError:
                raise ValueError(
                    f"Row {row_idx}, column {source_index}: missing weight value"
                )

        # Extract quota (last element)
        try:
            quota = _parse_number(row[weight_start + n], row_idx, weight_start + n, "quota")
        except IndexError:
            raise ValueError(
                f"Row {row_idx}, column {weight_start + n}: missing quota value"
            )

        matrix_data.append(weights)
        quotas_list.append(quota)

    # Validate: number of data rows must equal number of vertices (square matrix)
    if len(matrix_data) != n:
        raise ValueError(
            f"CSV matrix is not square: {len(matrix_data)} data rows but {n} vertices"
        )

    # Build quotas dict
    quotas = {}
    for i, v in enumerate(vertex_names):
        quotas[v] = quotas_list[i]

    # Build DataFrame (for compatibility)
    df = pd.DataFrame(matrix_data, index=vertex_names, columns=vertex_names)

    # Determine subset_size (default: n - 1, minimum 1)
    subset_size = max(1, n - 1)

    # Build networkx DiGraph
    graph = nx.DiGraph()
    for vertex in vertex_names:
        graph.add_node(vertex)

    for i, src in enumerate(vertex_names):
        for j, tgt in enumerate(vertex_names):
            weight = matrix_data[i][j]
            if weight != 0:
                graph.add_edge(src, tgt, weight=weight)

    return df, vertex_names, subset_size, quotas, graph