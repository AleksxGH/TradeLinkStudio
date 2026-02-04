from app.core.calculations import (
    get_copeland_indices,
    get_bundle_indices,
    get_pivotal_indices,
    get_pi_prime_indices,
    get_indices_shares
)
from app.core.result_builder import build_result_table

def calculate_all_indices(project):
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

    project.shares = {}
    for key, values in project.indices.items():
        project.shares[key] = get_indices_shares(values)

    project.results_df = build_result_table(project)