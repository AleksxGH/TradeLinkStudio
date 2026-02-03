import pandas as pd

def save_results(project, file_path: str):
    """
    Сохраняет результаты проекта в Excel, используя объект Project.

    :param project: объект Project с полями df_original, results, quotas
    :param file_path: путь для сохранения файла
    :return: путь к сохраненному файлу
    """
    if project.df_original is None or not project.results:
        raise ValueError("Project has no data or results to save!")

    df_out = project.df_original.copy()
    n_rows = df_out.shape[0]
    n_cols = df_out.shape[1]

    # Сохраняем вторую строку (квоты)
    row2_backup = df_out.loc[1].copy()

    # Добавляем новые пустые колонки справа
    for i in range(len(project.results)):
        df_out[n_cols + i] = [None] * n_rows

    # Заполняем новые колонки данными
    col_idx = n_cols
    for header, arr in project.results.items():
        df_out.iat[2, col_idx] = header  # заголовок на третьей строке
        for i, val in enumerate(arr):
            df_out.iat[3 + i, col_idx] = val
        col_idx += 1

    # Восстанавливаем вторую строку с квотами
    df_out.loc[1] = row2_backup

    if not file_path.endswith(".xlsx"):
        file_path += ".xlsx"

    df_out.to_excel(file_path, index=False, header=False)
    return file_path
