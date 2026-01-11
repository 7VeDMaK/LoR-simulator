from logic.battle_flow.clash_flow import ClashFlowMixin
from logic.battle_flow.targeting import calculate_redirections
from logic.battle_flow.lifecycle import prepare_turn, finalize_turn
from logic.battle_flow.executor import execute_single_action

class ClashSystem(ClashFlowMixin):
    """
    Уровень 3: Управление боем (Дирижер).
    Делегирует задачи специализированным модулям.
    """

    def __init__(self):
        self.logs = []

    def log(self, message):
        self.logs.append(message)

    # Статический метод для доступа из UI (precalculate_interactions)
    @staticmethod
    def calculate_redirections(atk_team: list, def_team: list):
        return calculate_redirections(atk_team, def_team)

    def prepare_turn(self, team_left: list, team_right: list):
        return prepare_turn(self, team_left, team_right)

    def execute_single_action(self, act, executed_slots):
        return execute_single_action(self, act, executed_slots)

    def finalize_turn(self, all_units: list):
        return finalize_turn(self, all_units)

    def resolve_turn(self, team_left: list, team_right: list):
        """
        ГЛАВНЫЙ МЕТОД (Pipeline).
        """
        full_report = []

        # 1. Подготовка
        init_logs, actions = self.prepare_turn(team_left, team_right)
        full_report.extend(init_logs)

        # Множество сыгранных слотов
        executed_slots = set()

        # 2. Выполнение
        for act in actions:
            logs = self.execute_single_action(act, executed_slots)
            full_report.extend(logs)

        # 3. Финализация
        end_logs = self.finalize_turn(team_left + team_right)
        full_report.extend(end_logs)

        return full_report