"""
ШАБЛОНЫ ТАЛАНТОВ ДЛЯ ПРОВЕРОК НАВЫКОВ

Используйте эти примеры для создания талантов, которые изменяют броски проверок.
"""

from logic.character_changing.talents.base_talent import BaseTalent


class TalentNoMistakes(BaseTalent):
    """
    Без Ошибок
    Все проверки используют формулу: 5 + d15 вместо обычного d6
    """
    id = "no_mistakes"
    name = "Без Ошибок"
    description = "Все проверки используют формулу: 5 + d15"
    
    def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
        """Изменяем параметры ВСЕХ проверок."""
        params["die_max"] = 15
        params["base_bonus"] = 5
        return params


class TalentSpeechMaster(BaseTalent):
    """
    Мастер Речи
    Проверки красноречия используют формулу: 10 + d10 + навык
    """
    id = "speech_master"
    name = "Мастер Речи"
    description = "Проверки красноречия: 10 + d10 + навык"
    
    def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
        """Изменяем только проверки красноречия."""
        if stat_key == "eloquence":
            params["die_max"] = 10
            params["base_bonus"] = 10
        return params


class TalentBrightTalent(BaseTalent):
    """
    Яркий Талант (Инженерия)
    Проверки инженерии используют формулу: 10 + d10 + навык
    Сложность проверок инженерии увеличена на 30%
    """
    id = "bright_talent"
    name = "Яркий Талант"
    description = "Проверки инженерии: 10 + d10 + навык, но DC × 1.3"
    
    def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
        """Изменяем проверки инженерии."""
        if stat_key == "engineering":
            params["die_max"] = 10
            params["base_bonus"] = 10
        return params


class TalentLuckyCharm(BaseTalent):
    """
    ПРИМЕР: Талисман Удачи
    Все проверки d6 становятся d8 (больше возможных результатов)
    """
    id = "lucky_charm"
    name = "Талисман Удачи"
    description = "Все d6 проверки становятся d8"
    
    def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
        """Улучшаем d6 броски до d8."""
        if params["die_max"] == 6:
            params["die_max"] = 8
        return params


class TalentFocusedMind(BaseTalent):
    """
    ПРИМЕР: Сфокусированный Разум
    +3 к проверкам мудрости и интеллекта
    """
    id = "focused_mind"
    name = "Сфокусированный Разум"
    description = "+3 к проверкам мудрости и интеллекта"
    
    def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
        """Добавляем бонус к ментальным проверкам."""
        if stat_key in ["wisdom", "intellect"]:
            params["base_bonus"] += 3
        return params


"""
ВАЖНО:
1. modify_check_parameters вызывается ПЕРЕД броском
2. После броска результат проходит через modify_skill_check_result от пассивок
3. Таким образом, талант меняет ТИП броска, а пассивки - РЕЗУЛЬТАТ

ПРИМЕР КОМБИНАЦИИ:
- Талант "Без Ошибок": бросаем 5 + d15
- Результат: 5 + 8 + 2 (стат) = 15
- Пассивка "Страх перед лечением" (medicine): 15 - 5 = 10
- Итог: 10
"""
