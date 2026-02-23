import numpy as np
from decimal import Decimal, getcontext
from itertools import combinations

class IndicesCalculator:
    def __init__(self, matrix, vertices, quotas, subset_size, precision=28):
        self.matrix = matrix
        self.vertices = vertices
        self.quotas = quotas
        self.subset_size = subset_size
        self.precision = precision

        self.bundle = {}
        self.pivotal = {}
        self.pi_prime = {}
        self.copeland = {}

        self._computed = False
        getcontext().prec = self.precision  # точность decimal

    # =========================
    # СБРОС КЭША
    # =========================
    def _invalidate(self):
        print("[DEBUG] Invalidating cache")
        self._computed = False

    # =========================
    # SETTERS
    # =========================
    def set_matrix(self, matrix):
        self.matrix = matrix
        self._invalidate()

    def set_vertices(self, vertices):
        self.vertices = vertices
        self._invalidate()

    def set_quotas(self, quotas):
        self.quotas = quotas
        self._invalidate()

    def set_subset_size(self, subset_size):
        self.subset_size = subset_size
        self._invalidate()

    def update_vertex(self, i, new_column=None, new_quota=None):
        try:
            print(f"[DEBUG] Updating vertex {i}")
            if new_column is not None:
                self.matrix[:, i] = new_column
                print(f"[DEBUG] Vertex {i} column updated")
            if new_quota is not None:
                self.quotas[i] = new_quota
                print(f"[DEBUG] Vertex {i} quota updated")
            self._invalidate()
        except Exception as e:
            print(f"[ERROR] update_vertex failed: {e}")

    # =========================
    # ГЛАВНЫЙ РАСЧЁТ
    # =========================
    def compute_all(self):
        try:
            print("[DEBUG] ===== START compute_all =====")
            self.bundle.clear()
            self.pivotal.clear()
            self.pi_prime.clear()
            self.copeland.clear()

            # ---------- Copeland ----------
            try:
                print("[DEBUG] Calculating Copeland")
                copeland_values = np.sum(self.matrix, axis=0).astype(np.float64)
                for v, val in zip(self.vertices, copeland_values):
                    self.copeland[v] = float(val)
                print("[DEBUG] Copeland done")
            except Exception as e:
                print(f"[ERROR] Copeland calculation failed: {e}")

            # ---------- Остальные индексы ----------
            for i, vertex in enumerate(self.vertices):
                try:
                    print(f"[DEBUG] Processing vertex {vertex} (index {i})")
                    col = self.matrix[:, i]
                    influencers = np.nonzero(col)[0]
                    values = [Decimal(str(col[j])) for j in influencers]  # decimal
                    quota = Decimal(str(self.quotas[i]))
                    print(f"[DEBUG] influencers count = {len(values)}, quota={quota}")

                    if len(values) == 0:
                        self.bundle[vertex] = 0.0
                        self.pivotal[vertex] = 0.0
                        self.pi_prime[vertex] = 0.0
                        continue

                    b, p, pp = self._analyze_all(values, quota)

                    self.bundle[vertex] = float(b)
                    self.pivotal[vertex] = float(p)
                    self.pi_prime[vertex] = float(pp)

                except Exception as e:
                    print(f"[ERROR] Processing vertex {vertex} failed: {e}")
                    self.bundle[vertex] = 0.0
                    self.pivotal[vertex] = 0.0
                    self.pi_prime[vertex] = 0.0

            self._computed = True
            print("[DEBUG] ===== FINISHED compute_all =====")
        except Exception as e:
            print(f"[ERROR] compute_all failed: {e}")
            self._computed = False

    # =========================
    # ПЕРЕБОР КОАЛИЦИЙ
    # =========================
    def _analyze_all(self, values, quota):
        getcontext().prec = 28

        n = len(values)
        max_size = min(self.subset_size, n)
        num_groups = 0  # обычный int
        pivotal_total = 0  # обычный int
        pi_prime_sum = 0  # обычный int

        quota_decimal = Decimal(str(quota))

        print(f"[DEBUG] _analyze_all: n={n}, max_size={max_size}, quota={quota_decimal}")

        try:
            for s in range(1, max_size + 1):
                for group in combinations(range(n), s):
                    # Сумма группы как Decimal
                    group_sum = sum(Decimal(str(values[idx])) for idx in group)

                    if group_sum >= quota_decimal:
                        num_groups += 1

                        # считаем пивотные вершины
                        pivotal_count = 0
                        for idx in group:
                            sum_without_j = group_sum - Decimal(str(values[idx]))
                            if sum_without_j < quota_decimal:
                                pivotal_count += 1

                        pivotal_total += pivotal_count
                        pi_prime_sum += pivotal_count * s

        except Exception as e:
            print(f"[ERROR] _analyze_all failed: {e}")

        print(
            f"[DEBUG] _analyze_all result: num_groups={num_groups}, pivotal_total={pivotal_total}, pi_prime_sum={pi_prime_sum}")
        return num_groups, pivotal_total, pi_prime_sum

    # =========================
    # GETTERS
    # =========================
    def _ensure_computed(self):
        if not self._computed:
            self.compute_all()

    def get_all_indices(self):
        self._ensure_computed()
        return {
            "bundle": self.bundle,
            "pivotal": self.pivotal,
            "pi_prime": self.pi_prime,
            "copeland": self.copeland
        }

    def get_bundle(self):
        self._ensure_computed()
        return self.bundle

    def get_pivotal(self):
        self._ensure_computed()
        return self.pivotal

    def get_pi_prime(self):
        self._ensure_computed()
        return self.pi_prime

    def get_copeland(self):
        self._ensure_computed()
        return self.copeland

    @staticmethod
    def get_indices_shares(indices):
        indices_sum = np.sum(indices).astype(np.float64)
        if indices_sum == 0:
            return np.zeros_like(indices)
        shares = indices / indices_sum
        return shares


