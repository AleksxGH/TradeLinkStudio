from app.core.calculations import (
    get_copeland_indices,
    get_bundle_indices,
    get_pivotal_indices,
    get_pi_prime_indices
)
from app.core.result_builder import build_results_table


def calculate_all_indices(project):

    copeland_dict = get_copeland_indices(project.matrix, project.vertices)
    bundle_dict = get_bundle_indices(
        project.matrix,
        project.vertices,
        project.quotas,
        project.subset_size
    )
    pivotal_dict = get_pivotal_indices(
        project.matrix,
        project.vertices,
        project.quotas,
        project.subset_size
    )
    pi_prime_dict = get_pi_prime_indices(
        project.matrix,
        project.vertices,
        project.quotas,
        project.subset_size
    )

    project.indices = {
        "copeland": list(copeland_dict.values()),
        "bundle": list(bundle_dict.values()),
        "pivotal": list(pivotal_dict.values()),
        "pi_prime": list(pi_prime_dict.values())
    }

    project.results_df = build_results_table(project)
