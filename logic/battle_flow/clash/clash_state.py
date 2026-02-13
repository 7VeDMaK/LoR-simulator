from core.logging import logger, LogLevel
from logic.battle_flow.clash.clash_utils import resolve_slot_die, store_remaining_dice


class ClashParticipantState:
    def __init__(self, unit, card, destruction_flag):
        self.unit = unit
        self.card = card
        self.queue = list(card.dice_list)
        self.idx = 0
        self.active_counter = None  # Tuple (die, source_is_counter)
        self.destroy_flag = destruction_flag

        # Текущее состояние для итерации
        self.current_die = None
        self.current_src_is_counter = False
        self.current_ctx = None

    def resolve_current_die(self):
        """Определяет текущий кубик для раунда."""
        # Проверяем, сломан ли текущий слот (destroy_flag только если мы еще в пределах очереди)
        is_break = self.destroy_flag if self.idx < len(self.queue) else False

        die, src = resolve_slot_die(
            self.unit, self.queue, self.idx,
            is_break, self.active_counter
        )

        self.current_die = die
        self.current_src_is_counter = src

        if die:
            self.unit.current_die = die

        return die

    def consume(self):
        if self.active_counter:
            self.active_counter = None
        else:
            # [FIX] Индекс должен расти ВСЕГДА, когда мы берем новый кубик из очереди,
            # независимо от того, контра это или атака.
            self.idx += 1

    def recycle(self):
        if not self.active_counter:
            # Сохраняем кубик как активный для следующего раунда
            self.active_counter = (self.current_die, self.current_src_is_counter)
            # [FIX] Сдвигаем индекс в карте, так как этот кубик "вышел" из своего слота
            self.idx += 1
            logger.log(f"{self.unit.name} recycled die", LogLevel.VERBOSE, "Clash")

    def has_dice_left(self):
        """Есть ли еще кубики в очереди или в counter."""
        return self.idx < len(self.queue) or self.active_counter is not None

    def store_remaining(self, report_list):
        """Сохраняет остатки после боя."""
        store_remaining_dice(self.unit, self.queue, self.idx, self.active_counter, report_list)

    def return_die(self, die):
        """[FIX] Возвращает кубик обратно в начало очереди (для сохранения контр-кубиков)."""
        if die:
            self.queue.insert(0, die)