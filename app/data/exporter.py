import pandas as pd
import os
from datetime import datetime


def save_results(project, file_path: str, matrix=None):
    """
    Export results using the same layout that `read_data.parse_xlsx` expects.

    Layout assumptions (0-based):
    - df.iloc[0,1] = number of vertices
    - df.iloc[1,3] = subset_size
    - quotas start at df.iloc[1,5:5+N]
    - vertex names are at df.iloc[2, 1:1+N]
    - matrix occupies rows df.iloc[3:3+N, 1:1+N]
    - we append indices as additional columns to the right of the matrix
    """
    if project.results_df is None or project.results_df.empty:
        raise ValueError("No results_df to export!")

    df = project.results_df.copy()
    vertices = list(getattr(project, "vertices", []))
    N = len(vertices)
    metrics = list(df.columns)
    M = len(metrics)

    # Determine number of columns: need at least (1 + N + M) and also ensure quotas start at col 5
    min_cols = max(1 + N + M, 5 + N)
    cols = list(range(min_cols))

    # Prepare empty grid
    rows_count = 3 + N  # header rows (0,1,2) + N matrix rows starting at row 3
    grid = [["" for _ in cols] for _ in range(rows_count)]

    # Row 0: number of vertices at column 1, with label in column 0
    grid[0][0] = "Number of vertices"
    grid[0][1] = int(N)

    # Row 1: project title in column 0, subset size and quotas with labels
    grid[1][0] = project.title
    grid[1][2] = "Subset size:"
    grid[1][3] = int(getattr(project, "subset_size", 0))
    grid[1][4] = "Quota values:"

    # Row 1: quotas starting at column 5 aligned to vertices order
    for i, v in enumerate(vertices):
        col_idx = 5 + i
        if col_idx < len(cols):
            qv = project.quotas.get(v, "")
            grid[1][col_idx] = float(qv) if qv != "" else ""

    # Row 2: vertex names starting at column 1 (with empty column 0)
    grid[2][0] = ""
    for i, v in enumerate(vertices):
        grid[2][1 + i] = v

    # Matrix: rows 3..3+N-1, cols 1..1+N-1
    # matrix argument may be a networkx.DiGraph, numpy array or pandas DataFrame
    matrix_vals = None
    try:
        import networkx as nx
        if matrix is None:
            matrix = None
        if isinstance(matrix, nx.DiGraph):
            import numpy as _np
            matrix_vals = nx.to_numpy_array(matrix, nodelist=vertices)
        elif hasattr(matrix, "to_numpy"):
            matrix_vals = matrix.to_numpy()
        else:
            matrix_vals = matrix
    except Exception:
        matrix_vals = matrix

    # If no matrix passed, leave original matrix area blank (user may not require it)
    if matrix_vals is not None:
        for i in range(N):
            for j in range(N):
                r = 3 + i
                c = 1 + j
                if r < rows_count and c < len(cols):
                    try:
                        grid[r][c] = matrix_vals[i][j]
                    except Exception:
                        grid[r][c] = matrix_vals[i][j] if matrix_vals is not None else ""

    # Запишем имена вершин в первую колонку (столбец 0) для каждой строки матрицы
    for i, v in enumerate(vertices):
        r = 3 + i
        if r < rows_count:
            grid[r][0] = v

    # Append indices to the right of the matrix (starting at column 1+N)
    start_idx_col = 1 + N
    # Ensure grid has enough columns to hold indices
    needed_cols = start_idx_col + M
    if needed_cols > len(cols):
        # extend each row
        extra = needed_cols - len(cols)
        for row in grid:
            row.extend([""] * extra)
        cols = list(range(len(grid[0])))

    # Header for metrics: place metric names on row 2 starting at start_idx_col
    for j, metric in enumerate(metrics):
        grid[2][start_idx_col + j] = metric

    # Fill metric values per vertex
    for i, v in enumerate(vertices):
        r = 3 + i
        for j, metric in enumerate(metrics):
            c = start_idx_col + j
            # Safely fetch value from df
            try:
                val = df.at[v, metric]
            except Exception:
                # fallback by position
                try:
                    val = df.iloc[i, j]
                except Exception:
                    val = ""
            grid[r][c] = val

    # Build DataFrame and write
    combined_df = pd.DataFrame(grid)

    if not file_path.endswith(".xlsx"):
        file_path += ".xlsx"

    try:
        combined_df.to_excel(file_path, index=False, header=False)
        return file_path
    except (PermissionError, OSError) as exc:
        # Попытка сохранить под альтернативным именем с временной меткой
        try:
            base, ext = os.path.splitext(file_path)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            alt_path = f"{base}_export_{ts}{ext}"
            combined_df.to_excel(alt_path, index=False, header=False)
            return alt_path
        except Exception:
            # Если и это не удалось, пробросим оригинальную ошибку
            raise exc
