class BudgetGuard:
    def __init__(self, monthly_limit=130):
        self.monthly_limit = monthly_limit
        self.current_usage = 0

    def add_usage(self, cost):
        self.current_usage += cost
        return self.current_usage

    def check_model(self):
        if self.current_usage > self.monthly_limit * 0.9:
            return "o4-mini"  # súper barato
        elif self.current_usage > self.monthly_limit * 0.5:
            return "gpt-5-mini"
        return "gpt-5"

