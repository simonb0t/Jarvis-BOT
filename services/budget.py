class BudgetGuard:
    """
    Guardián de costos simple:
    - Lleva conteo de uso "simulado" por operación (puedes enchufar costos reales si integras LLM).
    - Cambia el "modo" (alto/medio/bajo) según porcentaje del presupuesto mensual.
    """
    def __init__(self, monthly_limit=130.0):
        self.monthly_limit = float(monthly_limit)
        self.current_usage = 0.0

    def add_usage(self, cost: float):
        self.current_usage += float(cost)
        return self.current_usage

    def usage_ratio(self) -> float:
        if self.monthly_limit <= 0:
            return 1.0
        return self.current_usage / self.monthly_limit

    def check_mode(self) -> str:
        r = self.usage_ratio()
        if r >= 0.9:
            return "low"     # máximo ahorro
        if r >= 0.5:
            return "medium"  # ahorro moderado
        return "high"        # calidad alta (cuando hay presupuesto)
