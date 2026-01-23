

class MechanicsIteratorMixin:
    """
    Предоставляет методы для перебора всех активных механик юнита
    (Таланты, Пассивки, Аугментации, Статусы).
    """

    def _iter_all_mechanics(self):
        """
        Генератор, который перебирает все активные источники механик.
        Импорты внутри метода предотвращают циклические зависимости.
        """
        from logic.character_changing.talents import TALENT_REGISTRY
        from logic.character_changing.passives import PASSIVE_REGISTRY
        from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY
        from logic.statuses.status_definitions import STATUS_REGISTRY

        # 1. Таланты
        if hasattr(self, "talents"):
            for tid in self.talents:
                if tid in TALENT_REGISTRY: yield TALENT_REGISTRY[tid]

        # 2. Пассивки
        if hasattr(self, "passives"):
            for pid in self.passives:
                if pid in PASSIVE_REGISTRY: yield PASSIVE_REGISTRY[pid]

        # 3. Аугментации
        if hasattr(self, "augmentations"):
            for aid in self.augmentations:
                if aid in AUGMENTATION_REGISTRY: yield AUGMENTATION_REGISTRY[aid]

        # 4. Статусы
        if hasattr(self, "statuses"):
            for status_id, stack in self.statuses.items():
                if status_id in STATUS_REGISTRY:
                    yield STATUS_REGISTRY[status_id]