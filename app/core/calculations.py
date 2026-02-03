import numpy as np
from decimal import Decimal, getcontext
from itertools import combinations

def get_copeland_indices(matrix, vertices):
    copeland_values = np.sum(matrix, axis=0).astype(np.float64)
    copeland_dict = {vertex: value for vertex, value in zip(vertices, copeland_values)}
    return copeland_dict


def analyze_critical_groups(values, quota, max_group_size):
    getcontext().prec = 28

    num_critical_groups = 0
    num_pivotal_vertices = 0

    n = len(values)
    max_group_size = min(max_group_size, n)

    values_decimal = [Decimal(str(float(v))) for v in values]
    quota_decimal = Decimal(str(float(quota)))

    for s in range(1, max_group_size + 1):
        for group_indices in combinations(range(n), s):
            group_indices_list = list(group_indices)
            group_sum = Decimal('0')
            for idx in group_indices_list:
                group_sum += values_decimal[idx]

            if group_sum >= quota_decimal:
                num_critical_groups += 1

                for j in group_indices_list:
                    sum_without_j = group_sum - values_decimal[j]
                    if sum_without_j < quota_decimal:
                        num_pivotal_vertices += 1

    return float(num_critical_groups), float(num_pivotal_vertices)


def analyze_critical_groups_pi_prime(values, quota, max_group_size):
    getcontext().prec = 28

    num_critical_groups = 0
    pi_prime_sum = Decimal('0')

    n = len(values)
    max_group_size = min(max_group_size, n)

    values_decimal = [Decimal(str(float(v))) for v in values]
    quota_decimal = Decimal(str(float(quota)))

    for s in range(1, max_group_size + 1):
        for group_indices in combinations(range(n), s):
            group_indices_list = list(group_indices)
            group_sum = Decimal('0')
            for idx in group_indices_list:
                group_sum += values_decimal[idx]

            if group_sum >= quota_decimal:
                num_critical_groups += 1

                # Считаем пивотные вершины в этой группе
                pivotal_in_group = 0
                for j in group_indices_list:
                    sum_without_j = group_sum - values_decimal[j]
                    if sum_without_j < quota_decimal:
                        pivotal_in_group += 1

                # Добавляем: пивотные × размер группы
                pi_prime_sum += Decimal(str(pivotal_in_group)) * Decimal(str(s))

    return float(num_critical_groups), float(pi_prime_sum)


def get_bundle_indices(matrix, vertices, quotas, subset_size):
    bundle_indices = {}
    for i, vertex_name in enumerate(vertices):
        col = matrix[:, i]
        influencers = np.nonzero(col)[0]
        values = col[influencers].astype(np.float64)

        if len(values) == 0:
            bundle_indices[vertex_name] = np.float64(0)
            continue

        num_critical_groups, _ = analyze_critical_groups(values, quotas[i], subset_size)
        bundle_indices[vertex_name] = np.float64(num_critical_groups)

    return bundle_indices


def get_pivotal_indices(matrix, vertices, quotas, subset_size):
    pivotal_indices = {}
    for i, vertex_name in enumerate(vertices):
        col = matrix[:, i]
        influencers = np.nonzero(col)[0]
        values = col[influencers].astype(np.float64)

        if len(values) == 0:
            pivotal_indices[vertex_name] = np.float64(0)
            continue

        _, num_pivotal_vertices = analyze_critical_groups(values, quotas[i], subset_size)
        pivotal_indices[vertex_name] = np.float64(num_pivotal_vertices)

    return pivotal_indices


def get_pi_prime_indices(matrix, vertices, quotas, subset_size):
    pi_prime_indices = {}
    for i, vertex_name in enumerate(vertices):
        col = matrix[:, i]
        influencers = np.nonzero(col)[0]
        values = col[influencers].astype(np.float64)

        if len(values) == 0:
            pi_prime_indices[vertex_name] = np.float64(0)
            continue

        _, pi_prime_value = analyze_critical_groups_pi_prime(values, quotas[i], subset_size)
        pi_prime_indices[vertex_name] = np.float64(pi_prime_value)

    return pi_prime_indices


def get_indices_shares(indices):
    indices_sum = np.sum(indices).astype(np.float64)
    if indices_sum == 0:
        return np.zeros_like(indices)
    shares = indices / indices_sum
    return shares