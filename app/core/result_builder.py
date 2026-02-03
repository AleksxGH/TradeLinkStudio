import pandas as pd
import numpy as np
from app.core.calculations import get_indices_shares


def build_results_table(project):

    vertices = project.vertices
    subset_size = project.subset_size

    matrix_df = pd.DataFrame(
        project.matrix,
        index=vertices,
        columns=vertices
    )

    copeland = np.array(project.indices["copeland"])
    bundle = np.array(project.indices["bundle"])
    pivotal = np.array(project.indices["pivotal"])
    pi_prime = np.array(project.indices["pi_prime"])

    copeland_share = get_indices_shares(copeland)
    bundle_share = get_indices_shares(bundle)
    pivotal_share = get_indices_shares(pivotal)
    pi_prime_share = get_indices_shares(pi_prime)

    matrix_df["Copeland In index"] = copeland
    matrix_df[f"BI index, s={subset_size}"] = bundle
    matrix_df[f"PI index, s={subset_size}"] = pivotal
    matrix_df[f"PI' index size, s={subset_size}"] = pi_prime

    matrix_df["Copeland In index share"] = copeland_share
    matrix_df[f"BI index share, s={subset_size}"] = bundle_share
    matrix_df[f"PI index share, s={subset_size}"] = pivotal_share
    matrix_df[f"PI' index size share, s={subset_size}"] = pi_prime_share

    return matrix_df
