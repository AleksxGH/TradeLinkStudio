import pandas as pd

def save_results(project, file_path: str):
    if project.results_df is None or project.results_df.empty:
        raise ValueError("No results_df to export!")

    df = project.results_df.copy()
    n_cols = df.shape[1]

    # Первая колонка для индексов вершин
    columns = [""] + list(df.columns)

    # Первая строка: количество вершин
    row1 = pd.DataFrame([["Number of vertices", len(project.vertices)] + [""] * (n_cols - 1)],
                        columns=columns)

    # Вторая строка: subset size + quotas
    quotas_str = [str(q) for q in project.quotas]
    row2_values = [f"{project.title}", ""] + ["Subset size:", project.subset_size, "Quota values:"] + quotas_str
    # Заполняем пустыми до нужного количества столбцов
    while len(row2_values) < n_cols + 1:
        row2_values.append("")
    row2 = pd.DataFrame([row2_values], columns=columns)

    # Заголовки столбцов results_df
    header_row = pd.DataFrame([columns], columns=columns)

    # Данные results_df с индексом вершин
    data_df = df.copy()
    data_df.insert(0, "", df.index)

    # Объединяем все
    combined_df = pd.concat([row1, row2, header_row, data_df], ignore_index=True)

    if not file_path.endswith(".xlsx"):
        file_path += ".xlsx"

    combined_df.to_excel(file_path, index=False, header=False)
    return file_path
