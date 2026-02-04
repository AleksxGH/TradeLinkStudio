import pandas as pd
import numpy as np

def build_result_table(project):
    vertices = project.vertices
    subset_size = project.subset_size

    matrix_df = pd.DataFrame(
        project.matrix,
        index=vertices,
        columns=vertices
    )

    matrix_df["Copeland In index"] = np.array(project.indices["copeland"])
    matrix_df[f"BI index, s={subset_size}"] = np.array(project.indices["bundle"])
    matrix_df[f"PI index, s={subset_size}"] = np.array(project.indices["pivotal"])
    matrix_df[f"PI' index size, s={subset_size}"] = np.array(project.indices["pi_prime"])

    matrix_df["Copeland In index share"] = np.array(project.shares["copeland"])
    matrix_df[f"BI index share, s={subset_size}"] = np.array(project.shares["bundle"])
    matrix_df[f"PI index share, s={subset_size}"] =  np.array(project.shares["pivotal"])
    matrix_df[f"PI' index size share, s={subset_size}"] = np.array(project.shares["pi_prime"])

    return matrix_df