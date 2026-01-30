from logic.context import RollContext


class BaseEffect:
    """
    Единый базовый класс для всех игровых механик (Пассивки, Таланты, Статусы, Аугментации).
    Содержит заглушки для всех возможных событий и хуков.
    """
    id = "base"
    name = "Base Effect"
    description = ""

    # === БАЗОВЫЕ СОБЫТИЯ (Lifecycle) ===

    def on_combat_start(self, unit, *args, **kwargs):
        """
        Вызывается 1 раз в самом начале битвы, перед первым раундом.
        Пример: Пассивка 'Ветеран' (добавить 1 ед. Силы на весь бой), Талант 'Подготовка' (получить Свет).
        """
        pass

    def on_combat_end(self, unit, *args, **kwargs):
        """
        Вызывается 1 раз в конце битвы (победа или поражение).
        Пример: Очистка временных модификаторов, сохранение прогресса квеста.
        """
        pass

    def on_round_start(self, unit, *args, **kwargs):
        """
        Вызывается в начале каждого раунда (хода), до бросков скорости.
        Пример: BurnStatus (Ожог наносит урон), Regeneration (Лечение).
        """
        pass

    def on_speed_rolled(self, unit, *args, **kwargs):
        """
        Вызывается сразу после броска кубиков скорости, но до назначения атак.
        Пример: Пассивка 'Импульс' (если скорость 6+, получить Уклонение).
        """
        pass

    def on_round_end(self, unit, *args, **kwargs):
        """
        Вызывается в самом конце раунда, после всех атак.
        Пример: Снижение счетчика статусов (Duration -1), сброс временной Силы.
        """
        pass

    # === БОЕВЫЕ ТРИГГЕРЫ ===

    def on_roll(self, ctx: RollContext, **kwargs):
        """
        Вызывается непосредственно перед броском любого кубика (атаки или защиты).
        Пример: StrengthStatus (+Power к атаке), Paralysis (снижение силы).
        """
        pass

    def on_clash_win(self, ctx: RollContext, **kwargs):
        """
        Вызывается, когда юнит выигрывает столкновение (Clash).
        Пример: Пассивка 'Победный раж' (восстановить SP), наложение Paralysis на врага.
        """
        pass

    def on_clash_lose(self, ctx: RollContext, **kwargs):
        """
        Вызывается, когда юнит проигрывает столкновение.
        Пример: Пассивка 'Упорство' (получить Защиту на след. ход), 'Болевой порог'.
        """
        pass

    def on_clash_draw(self, ctx: RollContext, **kwargs):
        """
        Вызывается при ничьей в столкновении.
        Пример: Пассивка 'Равновесие' (восстановление Stagger).
        """
        pass

    def on_hit(self, ctx: RollContext, **kwargs):
        """
        Вызывается, когда кубик атаки успешно наносит урон (пробил защиту или удар по открытому).
        Пример: BleedStatus (наложить кровотечение), 'Вампиризм' (лечение от урона).
        """
        pass

    def on_take_damage(self, unit, amount, source, **kwargs):
        """
        Вызывается ПОСЛЕ того, как юнит получил урон (HP или Stagger вычтены).
        Пример: Reflection (отражение урона), Пассивка 'Месть' (Сила при получении урона).
        """
        pass

    # === АКТИВНЫЕ СПОСОБНОСТИ ===

    def activate(self, unit, *args, **kwargs):
        """
        Для способностей, которые игрок активирует вручную (E.G.O, активные таланты).
        """
        return False

    # === МОДИФИКАТОРЫ И ХУКИ ===

    def modify_stats(self, unit, stats: dict, *args):
        """
        Позволяет изменить базовые статы юнита при инициализации.
        Пример: Увеличение макс. HP от пассивки.
        """
        pass

    def modify_clash_interaction(self, ctx, interaction, loser_ctx):
        """
        Продвинутая логика изменения результата столкновения (редкий хук).
        """
        pass

    def modify_clash_interaction_loser(self, ctx, interaction, winner_ctx):
        pass

    def get_speed_dice_value_modifier(self, unit, stack=0) -> int:
        """
        Изменяет значение на кубике скорости (Инициатива).
        Пример: Haste (+Скорость), Bind (-Скорость).
        """
        return 0

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        """
        Возвращает словарь модификаторов статов для пересчета.
        Пример: {'max_hp': 10, 'initiative': 2}
        """
        return {}

    def get_speed_dice_bonus(self, unit, stack=0) -> int:
        """
        Добавляет дополнительные слоты скорости.
        Пример: +1 слот за каждые 3 скорости (механика 'Speed 3').
        """
        return 0

    def modify_active_slot(self, unit, slot, stack=0):
        """
        Позволяет изменить свойства конкретного слота скорости.
        Пример: Red Lycoris делает слот неперенаправляемым.
        """
        pass

    def modify_stagger_damage_multiplier(self, unit, multiplier: float) -> float:
        """
        Изменяет множитель урона по оглушенным целям (обычно x2.0).
        Пример: Пассивка 'Палач' (x2.5 урона по оглушенным).
        """
        return multiplier

    def calculate_level_growth(self, unit, stack=0) -> dict:
        """
        Для RPG системы: определяет прирост статов при повышении уровня.
        """
        pass

    def modify_satiety_penalties(self, unit, penalties: dict, stack=0) -> dict:
        """
        Для системы выживания: изменяет штрафы от голода.
        """
        return penalties

    def modify_incoming_damage(self, unit, amount: int, damage_type: str, stack=0, **kwargs) -> int:
        """
        Изменяет входящий урон ПЕРЕД расчетом резистов.
        Пример: Protection (-Урон), Fragile (+Урон), Stagger Resist.
        """
        return amount

    def on_before_status_add(self, unit, status_id, amount, stack=0):
        """
        Может отменить наложение статуса или изменить его количество.
        Возвращает (bool allowed, int new_amount).
        Пример: Иммунитет к огню (Burn).
        """
        return True, None

    def on_status_applied(self, unit, status_id, amount, duration=1, stack=0, **kwargs):
        """
        Триггер после успешного наложения статуса.
        Пример: 'Если наложили Ожог, восстановить 1 HP'.
        """
        pass

    def get_damage_modifier(self, unit, stack=0) -> float:
        """
        Возвращает множитель урона (%).
        Пример: +10% урона от всех источников.
        """
        return 0.0

    def apply_heal_reduction(self, unit, amount: int) -> int:
        """
        Снижает входящее лечение.
        Пример: Статус Deep Wound (Глубокая рана).
        """
        return amount

    # === ФЛАГИ И ПРОВЕРКИ (Boolean Checks) ===

    def can_redirect_on_equal_speed(self, unit) -> bool:
        """
        Разрешает перенаправление атаки при равной скорости (обычно нужно >).
        Пример: Пассивка 'Перехват'.
        """
        return False

    def prevents_dice_destruction_by_speed(self, unit) -> bool:
        """
        Запрещает уничтожение кубиков разницей в скорости.
        Пример: 'Непоколебимость'.
        """
        return False

    def prevents_specific_die_destruction(self, unit, die) -> bool:
        """
        Запрещает уничтожение конкретного кубика (например, Counter Die).
        """
        return False

    def can_use_counter_die_while_staggered(self, unit) -> bool:
        """
        Разрешает использовать контр-кубики даже в оглушении.
        """
        return False

    def can_break_empty_slot(self, unit) -> bool:
        """
        Разрешает ломать защиту врага, если у него пустой слот, но он защищается.
        Пример: Талант 'Изучение поведения'.
        """
        return False

    def prevents_death(self, unit, stack=0) -> bool:
        """
        Запрещает смерть (HP не падает ниже 1).
        Пример: Пассивка 'Бессмертие'.
        """
        return False

    def prevents_stagger(self, unit, stack=0) -> bool:
        """
        Запрещает переход в состояние оглушения (Stagger).
        Пример: Пассивка 'Железная воля'.
        """
        return False

    def prevents_surprise_attack(self, unit) -> bool:
        """
        Защита от внезапных атак (первого хода).
        """
        return False

    # === НОВЫЕ ХУКИ УРОНА (Refactored Damage Pipeline) ===

    def modify_resistance(self, unit, res: float, damage_type: str, dice=None, stack=0, log_list=None) -> float:
        """
        Изменяет множитель сопротивления (Resistance).
        Вызывается после базовых резистов, но перед расчетом финального числа.
        Пример: AdaptationStatus (Адаптация снижает множитель до 0.25).
        """
        return res

    def absorb_damage(self, unit: object, amount: int, damage_type: str, stack: object = 0, log_list: object = None) -> int:
        """
        Поглощает финальный урон (после защиты и резистов), тратя ресурс эффекта.
        Пример: BarrierStatus (поглощает X урона, тратит X стаков).
        """
        return amount

    def prevents_damage(self, unit, attacker_ctx) -> bool:
        """
        Полный иммунитет к получению урона (предотвращает даже on_hit триггеры).
        Пример: RedLycorisStatus.
        """
        return False

    def modify_outgoing_damage(self, unit, amount: int, damage_type: str, stack=0, log_list=None) -> int:
        """
        Изменяет исходящий урон перед его нанесением.
        Пример: DmgUp (+урон), DmgDown (-урон), пассивки на % урона.
        """
        return amount

    def on_skill_check(self, unit, check_result: int, stat_key: str, **kwargs):
        """
        ТОЧКА 3: Вызывается ПОСЛЕ совершения проверки навыка/характеристики.
        Используется для триггеров и эффектов, зависящих от результата.
        
        Args:
            unit: юнит, совершивший проверку
            check_result: ИТОГОВОЕ значение броска (после всех модификаторов)
            stat_key: название навыка: "strength", "medicine" и т.д.
        
        ШАБЛОН ИСПОЛЬЗОВАНИЯ:
        ```python
        def on_skill_check(self, unit, check_result: int, stat_key: str, **kwargs):
            if stat_key == "medicine" and check_result >= 15:
                # Если успешная проверка медицины
                unit.add_status("heal_bonus", 1, duration=2)
            
            if stat_key == "luck":
                # Реагируем на любую проверку удачи
                unit.resources["luck_uses"] = unit.resources.get("luck_uses", 0) + 1
        ```
        """
        pass

    def modify_skill_check_result(self, unit, stat_key: str, current_result: int) -> int:
        """
        ТОЧКА 2: Модифицирует ИТОГОВЫЙ результат проверки навыка/характеристики.
        Вызывается ПОСЛЕ броска кубика и добавления базовых модификаторов.
        
        Args:
            unit: юнит, совершающий проверку
            stat_key: название навыка: "strength", "medicine", "luck" и т.д.
            current_result: текущий результат (бросок + модификатор стата + бонус)
        
        Returns:
            int: НОВЫЙ результат (не модификатор, а полное значение!)
        
        ШАБЛОН ИСПОЛЬЗОВАНИЯ:
        ```python
        def modify_skill_check_result(self, unit, stat_key: str, current_result: int) -> int:
            if stat_key == "medicine":
                return current_result - 5  # Штраф -5 к медицине
            
            if stat_key == "psych":
                return current_result + 4  # Бонус +4 к психике
            
            return current_result  # Обязательно вернуть результат!
        ```
        """
        return current_result

    def override_roll_base_stat(self, unit, current_pair, dice=None, **kwargs):
        """
        Позволяет изменить базовую характеристику, от которой зависит бросок.
        current_pair: (value, name_of_stat), например (30, 'Strength')
        Returns: (new_value, new_name)
        Пример: 'Доступ к истокам' заменяет Силу/Стойкость на Удачу.
        """
        return current_pair

    def on_check_roll(self, unit, attribute, context, **kwargs):
        """
        ТОЧКА 1: Вызывается ПЕРЕД броском проверки навыка (Skill Check).
        Используется для добавления Advantage/Disadvantage.
        
        Args:
            unit: юнит, совершающий проверку
            attribute: название навыка (строка): "strength", "medicine", "eloquence" и т.д.
            context: объект CheckContext с флагами is_advantage / is_disadvantage
            **kwargs: дополнительные параметры (например, stack для статусов)
        
        ШАБЛОН ИСПОЛЬЗОВАНИЯ:
        ```python
        def on_check_roll(self, unit, attribute, context, **kwargs):
            if attribute == "medicine":  # Проверка конкретного навыка
                context.is_advantage = True  # Даем преимущество
            
            if attribute in ["strength", "endurance"]:  # Несколько навыков
                context.is_disadvantage = True  # Даем помеху
        ```
        """
        pass

    def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
        """
        ТОЧКА 1.5: Модифицирует параметры броска ДО его выполнения.
        Используется талантами для изменения типа кубика и базовых бонусов.
        
        Args:
            unit: юнит, совершающий проверку
            stat_key: название навыка
            params: словарь с параметрами {
                "die_max": int,      # Максимум на кубике (6, 12, 15, 20)
                "die_min": int,      # Минимум на кубике (обычно 1)
                "base_bonus": int,   # Базовый бонус (например, +5 от таланта)
                "stat_bonus": int    # Бонус от характеристики
            }
        
        Returns:
            dict: НОВЫЕ параметры (измените нужные поля)
        
        ШАБЛОН ИСПОЛЬЗОВАНИЯ (Талант):
        ```python
        def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
            # Талант "Без Ошибок": 5 + d15 вместо обычного d6
            params["die_max"] = 15
            params["base_bonus"] = 5
            return params
        
        # Талант "Мастер речи": d10 + 10 для красноречия
        def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
            if stat_key == "eloquence":
                params["die_max"] = 10
                params["base_bonus"] = 10
            return params
        ```
        """
        return params
        pass