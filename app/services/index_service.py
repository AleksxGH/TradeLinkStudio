from app.core.calculations import (
    get_copeland_indices,
    get_bundle_indices,
    get_pivotal_indices,
    get_pi_prime_indices
)
from app.core.result_builder import build_results_table

import numpy as np

def calculate_all_indices(project):
    # Считаем абсолютные индексы
    copeland_dict = get_copeland_indices(project.matrix, project.vertices)
    bundle_dict = get_bundle_indices(project.matrix, project.vertices, project.quotas, project.subset_size)
    pivotal_dict = get_pivotal_indices(project.matrix, project.vertices, project.quotas, project.subset_size)
    pi_prime_dict = get_pi_prime_indices(project.matrix, project.vertices, project.quotas, project.subset_size)

    project.indices = {
        "copeland": [copeland_dict[v] for v in project.vertices],
        "bundle": [bundle_dict[v] for v in project.vertices],
        "pivotal": [pivotal_dict[v] for v in project.vertices],
        "pi_prime": [pi_prime_dict[v] for v in project.vertices]
    }

    # Считаем shares (доли)
    project.shares = {}
    for key, values in project.indices.items():
        arr = np.array(values, dtype=np.float64)
        total = arr.sum()
        project.shares[key] = (arr / total if total != 0 else np.zeros_like(arr)).tolist()

    # Создаём DataFrame для UI (с абсолютными и долевыми индексами)
    project.results_df = build_results_table(project)

    # Сохраняем словарь для экспорта
    project.results = {
        "Copeland In index": project.indices["copeland"],
        f"BI index, s={project.subset_size}": project.indices["bundle"],
        f"PI index, s={project.subset_size}": project.indices["pivotal"],
        f"PI' index size, s={project.subset_size}": project.indices["pi_prime"],
        "Copeland In index share": project.shares["copeland"],
        f"BI index share, s={project.subset_size}": project.shares["bundle"],
        f"PI index share, s={project.subset_size}": project.shares["pivotal"],
        f"PI' index size share, s={project.subset_size}": project.shares["pi_prime"],
    }