from app.core.indices_calculator import IndicesCalculator


class ComputeEngine:
    """Вычислительный движок для обработки данных проекта"""

    @staticmethod
    def compute(state, config=None):
        """
        Вычисляет индексы на основе состояния
        
        Args:
            state: словарь с ключами matrix, vertices, quotas, subset_size
            config: настройки приложения
            
        Returns:
            словарь с результатами вычисления или None при ошибке
        """
        if not state:
            return None

        try:
            graph = state.get("matrix")
            vertices = state.get("vertices")
            quotas = state.get("quotas")
            subset_size = state.get("subset_size")

            if not all([graph, vertices, quotas is not None, subset_size]):
                return None

            calculator = IndicesCalculator(graph, vertices, quotas, subset_size)
            calculator.calculate_all()

            result = {
                "copeland": calculator.get_copeland(),
                "bundle": calculator.get_bundle(),
                "pivotal": calculator.get_pivotal(),
                "pi_prime": calculator.get_pi_prime()
            }

            # Нормализованные версии считаем всегда; показ управляется UI-переключателями.
            result["copeland_norm"] = IndicesCalculator.get_indices_shares(result["copeland"])
            result["bundle_norm"] = IndicesCalculator.get_indices_shares(result["bundle"])
            result["pivotal_norm"] = IndicesCalculator.get_indices_shares(result["pivotal"])
            result["pi_prime_norm"] = IndicesCalculator.get_indices_shares(result["pi_prime"])

            return result

        except Exception as e:
            print(f"[ComputeEngine] Error: {e}")
            import traceback
            traceback.print_exc()
            return None

