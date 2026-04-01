import networkx as nx
from itertools import combinations

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
        G = self._ensure_directed()

        centrality = {node: 0 for node in G.nodes()}

        for node in G.nodes():
            in_edges = list(G.in_edges(node, data='weight', default=1))
            m = len(in_edges)

            if m == 0:
                continue

            max_group_size = min(self.subset_size, m)
            for group_size in range(1, max_group_size + 1):
                for edge_group in combinations(in_edges, group_size):
                    total_weight = sum(weight for _, _, weight in edge_group)
                    if total_weight >= self.quotas.get(node, 0):
                        centrality[node] += 1

        return centrality

    def pivotal_index(self, weighted_version=True):
        G = self._ensure_directed()

        pivotal_counts = {node: 0 for node in G.nodes()}

        for node in G.nodes():
            in_edges = list(G.in_edges(node, data='weight', default=1))
            m = len(in_edges)

            if m == 0:
                continue

            max_group_size = min(self.subset_size, m)
            for group_size in range(1, max_group_size + 1):
                for edge_group in combinations(in_edges, group_size):
                    total_weight = sum(w for _, _, w in edge_group)

                    if total_weight < self.quotas.get(node, 0):
                        continue

                    for _, u, w in edge_group:
                        if (total_weight - w) < self.quotas.get(node, 0):
                            increment = group_size if weighted_version else 1
                            pivotal_counts[u] += increment

        return pivotal_counts

    def calculate_all(self):
        try:
            self.bundle.clear()
            self.pivotal.clear()
            self.pi_prime.clear()
            self.copeland.clear()

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
        total = sum(indices.values())
        if total > 0:
            return [score / total for score in indices.values()]
        return [0.0 for _ in indices]