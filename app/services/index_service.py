from app.core.indices_calculator import IndicesCalculator
from app.core.result_builder import build_result_table

def calculate_all_indices(project):
    calc = IndicesCalculator(project.graph, project.vertices, project.quotas, project.subset_size)

    copeland_dict = calc.get_copeland()
    bundle_dict = calc.get_bundle()
    pivotal_dict = calc.get_pivotal()
    pi_prime_dict = calc.get_pi_prime()

    project.indices = {
        "copeland": [copeland_dict[v] for v in project.vertices],
        "bundle": [bundle_dict[v] for v in project.vertices],
        "pivotal": [pivotal_dict[v] for v in project.vertices],
        "pi_prime": [pi_prime_dict[v] for v in project.vertices]
    }

    project.shares = {
        "copeland": IndicesCalculator.get_indices_shares(copeland_dict),
        "bundle": IndicesCalculator.get_indices_shares(bundle_dict),
        "pivotal": IndicesCalculator.get_indices_shares(pivotal_dict),
        "pi_prime": IndicesCalculator.get_indices_shares(pi_prime_dict)
    }

    project.results_df = build_result_table(project)