import networkx as nx
from itertools import combinations
import numpy as np

class IndicesCalculator:
    def __init__(self, graph, vertices, quotas, subset_size):
        self.graph = graph
        self.vertices = vertices
        self.quotas = quotas
        self.subset_size = subset_size

        self.bundle = {}
        self.pivotal = {}
        self.pi_prime = {}
        self.copeland = {}

        self._computed = False

    def _invalidate(self):
        self._computed = False

    def set_graph(self, graph):
        self.graph = graph
        self._invalidate()

    def set_vertices(self, vertices):
        self.vertices = vertices
        self._invalidate()

    def set_subset_size(self, subset_size):
        self.subset_size = subset_size
        self._invalidate()

    def copeland_index(self):
        """Copeland Index: сумма весов входящих рёбер для каждой вершины"""
        copeland = {}
        for node in self.vertices:
            total_weight = sum(
                data.get('weight', 1)
                for _, _, data in self.graph.in_edges(node, data=True)
            )
            copeland[node] = total_weight
        return copeland

    def _ensure_directed(self):
        """Возвращает ориентированную версию графа, не изменяя исходный"""
        if isinstance(self.graph, nx.DiGraph):
            return self.graph
        else:
            return self.graph.to_directed()

    def bundle_index(self):
        """Bundle Index: количество критических групп входящих соседей размером <= k"""
        G = self._ensure_directed()
        bundle = {node: 0 for node in G.nodes()}

        for node in G.nodes():
            in_edges = list(G.in_edges(node, data='weight', default=1))
            m = len(in_edges)

            if m == 0:
                continue

            quota = self.quotas.get(node, 0)
            max_group_size = min(self.subset_size, m)

            # Перебираем все возможные группы размером от 1 до max_group_size
            for group_size in range(1, max_group_size + 1):
                for edge_group in combinations(in_edges, group_size):
                    total_weight = sum(weight for _, _, weight in edge_group)
                    # Если группа критична (вес >= квота), добавляем 1
                    if total_weight >= quota:
                        bundle[node] += 1

        return bundle

    def pivotal_index(self, weighted_version=False):
        """
        Pivotal Index: количество pivotal-узлов (узлов, чьё участие критично)
        
        Узел v в группе S считается pivotal, если:
        - sum(weights in S) >= quota (группа критична)
        - sum(weights in S \ {v}) < quota (без v группа не критична)
        
        weighted_version=False: каждый pivotal-узел добавляет 1
        weighted_version=True: каждый pivotal-узел добавляет размер группы
        """
        G = self._ensure_directed()
        pivotal = {node: 0 for node in G.nodes()}

        for node in G.nodes():
            in_edges = list(G.in_edges(node, data='weight', default=1))
            m = len(in_edges)

            if m == 0:
                continue

            quota = self.quotas.get(node, 0)
            max_group_size = min(self.subset_size, m)

            # Перебираем все возможные группы размером от 1 до max_group_size
            for group_size in range(1, max_group_size + 1):
                for edge_group in combinations(in_edges, group_size):
                    total_weight = sum(w for _, _, w in edge_group)

                    # Проверяем, является ли группа критической
                    if total_weight < quota:
                        continue

                    # Для каждого узла в группе проверяем, является ли он pivotal
                    for source, target, weight in edge_group:
                        weight_without_this_edge = total_weight - weight

                        # Если без этого узла группа не критична, он pivotal
                        if weight_without_this_edge < quota:
                            if weighted_version:
                                # Добавляем размер группы (количество рёбер в группе)
                                pivotal[node] += group_size
                            else:
                                # Просто добавляем 1
                                pivotal[node] += 1

        return pivotal

    def calculate_all(self):
        try:
            self.bundle.clear()
            self.pivotal.clear()
            self.pi_prime.clear()
            self.copeland.clear()

            matrix = nx.to_numpy_array(self.graph, nodelist=self.vertices)
            print(matrix)

            self.copeland = self.copeland_index()
            self.bundle = self.bundle_index()
            self.pivotal = self.pivotal_index(weighted_version=False)
            self.pi_prime = self.pivotal_index(weighted_version=True)

            self._computed = True

        except Exception as e:
            print(f"[ERROR] calculate_all failed: {e}")
            import traceback
            traceback.print_exc()
            self._computed = False

    # =========================
    # GETTERS
    # =========================
    def _ensure_computed(self):
        if not self._computed:
            self.calculate_all()

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
        """Нормализованные значения индексов (сумма = 1)"""
        total = sum(indices.values())
        if total > 0:
            return [score / total for score in indices.values()]
        return [0.0 for _ in indices]
