# core/unit_mixins.py
import random
from typing import Dict, TYPE_CHECKING
from core.enums import DiceType
# Импортируем классы для создания карт на лету
from core.card import Card
from core.dice import Dice

if TYPE_CHECKING:
    pass


class UnitStatusMixin:
    # ... (код без изменений) ...
    def _ensure_status_storage(self):
        if not hasattr(self, "_status_effects"): self._status_effects = {}
        if not hasattr(self, "delayed_queue"): self.delayed_queue = []

    @property
    def statuses(self) -> Dict[str, int]:
        self._ensure_status_storage()
        summary = {}
        for name, instances in self._status_effects.items():
            total = sum(i["amount"] for i in instances)
            if total > 0:
                summary[name] = total
        return summary

        # === ОБНОВЛЕНИЕ: Добавлен аргумент trigger_events ===
    def add_status(self, name: str, amount: int, duration: int = 1, delay: int = 0, trigger_events: bool = True):
        self._ensure_status_storage()
        if amount <= 0: return False, None # Возвращаем статус неудачи

        from logic.talents import TALENT_REGISTRY
        for tid in self.talents:
            if tid in TALENT_REGISTRY:
                if hasattr(TALENT_REGISTRY[tid], "on_before_status_add"):
                    # Получаем результат
                    res = TALENT_REGISTRY[tid].on_before_status_add(self, name, amount)

                    # Поддержка старого (bool) и нового (tuple) формата
                    if isinstance(res, tuple):
                        allowed, msg = res
                    else:
                        allowed, msg = res, None

                    if not allowed:
                        return False, msg  # Возвращаем причину блокировки

        # 2. Проверка через пассивки (аналогично)
        from logic.passives import PASSIVE_REGISTRY
        for pid in self.passives:
            if pid in PASSIVE_REGISTRY:
                if hasattr(PASSIVE_REGISTRY[pid], "on_before_status_add"):
                    res = PASSIVE_REGISTRY[pid].on_before_status_add(self, name, amount)

                    if isinstance(res, tuple):
                        allowed, msg = res
                    else:
                        allowed, msg = res, None

                    if not allowed:
                        return False, msg

        if delay > 0:
            self.delayed_queue.append({
                "name": name, "amount": amount, "duration": duration, "delay": delay
            })
            return True, "Delayed"  # Успех (отложенный)

        if name not in self._status_effects:
            self._status_effects[name] = []

        self._status_effects[name].append({"amount": amount, "duration": duration})

        # === НОВЫЙ ХУК: on_status_applied ===
        if trigger_events:
            # Вызываем хук у талантов
            for tid in self.talents:
                if tid in TALENT_REGISTRY and hasattr(TALENT_REGISTRY[tid], "on_status_applied"):
                    TALENT_REGISTRY[tid].on_status_applied(self, name, amount, duration=duration)

            # Вызываем хук у пассивок
            for pid in self.passives:
                if pid in PASSIVE_REGISTRY and hasattr(PASSIVE_REGISTRY[pid], "on_status_applied"):
                    PASSIVE_REGISTRY[pid].on_status_applied(self, name, amount, duration=duration)

        return True, None  # Успех

    def get_status(self, name: str) -> int:
        self._ensure_status_storage()
        if name not in self._status_effects: return 0
        return sum(i["amount"] for i in self._status_effects[name])

    def remove_status(self, name: str, amount: int = None):
        self._ensure_status_storage()
        if name not in self._status_effects: return

        if amount is None:
            del self._status_effects[name]
            return

        items = sorted(self._status_effects[name], key=lambda x: x["duration"])
        rem = amount
        new_items = []

        for item in items:
            if rem <= 0:
                new_items.append(item)
                continue
            if item["amount"] > rem:
                item["amount"] -= rem
                rem = 0
                new_items.append(item)
            else:
                rem -= item["amount"]

        if not new_items:
            del self._status_effects[name]
        else:
            self._status_effects[name] = new_items


class UnitCombatMixin:
    """
    Боевая логика: броски инициативы, проверки состояния.
    """

    def roll_speed_dice(self):
        """Генерация активных слотов на раунд."""
        self.active_slots = []

        if self.is_dead():
            return

        # 1. Основные кубики (расчитанные из статов)
        for (d_min, d_max) in self.computed_speed_dice:
            mod = self.get_status("haste") - self.get_status("slow") - self.get_status("bind")
            val = max(1, random.randint(d_min, d_max) + mod)
            self.active_slots.append({
                'speed': val, 'card': None, 'target_slot': None, 'is_aggro': False
            })

        # 2. Активные способности (Ярость - Berserker Rage)
        if self.active_buffs.get("berserker_rage", 0) > 0:
            d_min, d_max = self.computed_speed_dice[0] if self.computed_speed_dice else (self.base_speed_min,
                                                                                         self.base_speed_max)
            mod = self.get_status("haste") - self.get_status("slow") - self.get_status("bind")
            val = max(1, random.randint(d_min, d_max) + mod)

            self.active_slots.append({
                'speed': val, 'card': None, 'target_slot': None, 'is_aggro': False,
                'source_effect': 'Rage 😡'
            })

        # 3. ТАЛАНТ: НЕИСТОВСТВО (Frenzy) - ИСПРАВЛЕННОЕ СКАЛИРОВАНИЕ
        if "frenzy" in self.talents:
            # === ИСПРАВЛЕНИЕ: Берем сильнейший кубик, как в Ярости ===
            if self.computed_speed_dice:
                d_min, d_max = self.computed_speed_dice[0]
            else:
                d_min, d_max = self.base_speed_min, self.base_speed_max
            # ========================================================

            mod = self.get_status("haste") - self.get_status("slow") - self.get_status("bind")

            # --- Слот 1: Контр-кубик (5-7) ---
            val1 = max(1, random.randint(d_min, d_max) + mod)

            card_frenzy_1 = Card(
                id="frenzy_counter_1", name="Counter (5-7)", tier=1, card_type="melee",
                description="Counter Die: Перехватывает односторонние атаки.",
                dice_list=[Dice(5, 7, DiceType.SLASH, is_counter=True)]
            )

            self.active_slots.append({
                'speed': val1,
                'card': card_frenzy_1,
                'target_slot': None,
                'is_aggro': False,
                'source_effect': 'Counter ⚡',
                'locked': True
            })

            # --- Слот 2: Если Self-Control > 10 (6-8) ---
            if self.get_status("self_control") > 10:
                val2 = max(1, random.randint(d_min, d_max) + mod)

                card_frenzy_2 = Card(
                    id="frenzy_counter_2", name="Counter II (6-8)", tier=2, card_type="melee",
                    description="Counter Die: Перехватывает односторонние атаки.",
                    dice_list=[Dice(6, 8, DiceType.SLASH, is_counter=True)]
                )

                self.active_slots.append({
                    'speed': val2,
                    'card': card_frenzy_2,
                    'target_slot': None,
                    'is_aggro': False,
                    'source_effect': 'Counter+ ⚡',
                    'locked': True
                })

        if self.get_status("red_lycoris") > 0:
            for slot in self.active_slots:
                slot['prevent_redirection'] = True
                # Визуальная пометка для игрока
                if not slot.get('source_effect'):
                    slot['source_effect'] = "Lycoris 🩸"

        # === ТАЛАНТ: МАХНУТЬ ХВОСТИКОМ (Tail Swipe) ===
        if "wag_tail" in self.passives:
            # Берем значения скорости как для основного кубика
            if self.computed_speed_dice:
                d_min, d_max = self.computed_speed_dice[0]
            else:
                d_min, d_max = self.base_speed_min, self.base_speed_max

            mod = self.get_status("haste") - self.get_status("slow") - self.get_status("bind")
            val_tail = max(1, random.randint(d_min, d_max) + mod)

            # Создаем техническую карту с контр-кубиком (Уклонение 5-7)
            card_tail = Card(
                id="tail_swipe_counter",
                name="Tail Counter",
                description="Counter Evade: Отражает атаку и сгорает.",
                dice_list=[Dice(5, 7, DiceType.EVADE, is_counter=True)]
            )

            # Добавляем отдельный слот
            self.active_slots.append({
                'speed': val_tail,
                'card': card_tail,
                'target_slot': -1,
                'is_aggro': False,
                'source_effect': 'Tail Swipe 🐈',
                'locked': True,  # Запрещаем менять карту в симуляторе
                'consumed': False
            })

            # === 3.2 ОБОРОНА (ZAFU STYLE) ===
            # Проверяем наличие навыка (в passives или talents, в зависимости от того, куда вы его записали)
        if "defense_zafu" in self.talents:

            # 1. Собираем список кубиков (Dice List)
            zafu_dice_list = []

            # -- Базовый кубик (3.2) --
            zafu_dice_list.append(Dice(5, 7, DiceType.BLOCK, is_counter=False))

            # -- Талант 3.5: +1 Кубик Блока --
            if "talent_3_5" in self.talents:
                zafu_dice_list.append(Dice(5, 7, DiceType.BLOCK, is_counter=False))

            # -- Талант 3.8: +1 Кубик Блока --
            if "talent_3_8" in self.talents:
                zafu_dice_list.append(Dice(5, 7, DiceType.BLOCK, is_counter=False))

            # -- Талант 3.10: +1 Кубик Контр-Блока --
            # Добавляем его в ту же карту (как 4-й кубик), если он относится к этому навыку
            if "talent_3_10" in self.talents:
                zafu_dice_list.append(Dice(5, 7, DiceType.BLOCK, is_counter=True))

            # 2. Создаем ОДНУ карту, содержащую все эти кубики
            card_zafu_block = Card(
                id="zafu_block_card",
                name="Зафу: Оборона",
                tier=1,
                card_type="melee",
                description="Неизменяемая защита.",
                flags=["unchangeable"],
                dice_list=zafu_dice_list  # <--- Передаем собранный список
            )

            # 3. Рассчитываем скорость (один раз)
            if self.computed_speed_dice:
                d_min, d_max = self.computed_speed_dice[0]
            else:
                d_min, d_max = self.base_speed_min, self.base_speed_max

            mod = self.get_status("haste") - self.get_status("slow") - self.get_status("bind")
            val_spd = max(1, random.randint(d_min, d_max) + mod)

            # 4. Добавляем ОДИН слот с этой картой
            self.active_slots.append({
                'speed': val_spd,
                'card': card_zafu_block,
                'target_slot': None,
                'is_aggro': False,
                'source_effect': 'Defense 🛡️',
                'locked': True
            })

    def is_staggered(self) -> bool:
        if self.get_status("red_lycoris") > 0:
            return False
        return self.current_stagger <= 0

    def is_dead(self) -> bool:
        if self.get_status("red_lycoris") > 0:
            return False

        return self.current_hp <= 0


class UnitLifecycleMixin:
    def heal_hp(self, amount: int) -> int:
        # === FIX: Использование get_modded_value для работы с новой структурой модов (dict) ===
        # get_modded_value(base_val, name, mods) -> (base + flat) * (1 + pct/100)
        # Здесь base_val = amount
        from logic.calculations.formulas import get_modded_value
        final_amt = get_modded_value(amount, "heal_efficiency", self.modifiers)

        # Обработка глубокой раны
        if self.get_status("deep_wound") > 0:
            final_amt = int(final_amt * 0.75)
            self.remove_status("deep_wound", 1)

        self.current_hp = min(self.max_hp, self.current_hp + final_amt)
        return final_amt

    # === [NEW] Added restore_sp method ===
    def restore_sp(self, amount: int) -> int:
        if amount <= 0: return 0

        # Calculate how much can be restored
        # Can restore from panic (negative SP) up to max_sp
        final_sp = min(self.max_sp, self.current_sp + amount)
        recovered = final_sp - self.current_sp

        self.current_sp = final_sp
        return recovered

    def take_sanity_damage(self, amount: int):
        self.current_sp = max(-45, self.current_sp - amount)

        # core/unit_mixins.py

    def tick_cooldowns(self):
        # 1. Активные способности (Таланты)
        for k in list(self.cooldowns.keys()):
            self.cooldowns[k] -= 1
            if self.cooldowns[k] <= 0: del self.cooldowns[k]

        # 2. Баффы
        for k in list(self.active_buffs.keys()):
            self.active_buffs[k] -= 1
            if self.active_buffs[k] <= 0: del self.active_buffs[k]

        # 3. [НОВОЕ] Откаты карт
        for cid in list(self.card_cooldowns.keys()):
            self.card_cooldowns[cid] -= 1
            if self.card_cooldowns[cid] <= 0:
                del self.card_cooldowns[cid]

        if self.is_dead():
            self.active_buffs.clear()
            self.card_cooldowns.clear()