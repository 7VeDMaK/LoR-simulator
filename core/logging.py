import os
from datetime import datetime
from enum import IntEnum

_memory_log_storage = []


def _get_session_state():
    try:
        import streamlit as st
    except Exception:
        return None
    return getattr(st, "session_state", None)

# Путь к файлу полного лога
LOG_FILE_PATH = "data/logs/full_battle_log.txt"


class LogLevel(IntEnum):
    """
    Уровни детализации логов.
    """
    MINIMAL = 1  # Уровень 1: Только важные итоги (Нанесенный урон, Смерть, Результат столкновения)
    NORMAL = 2  # Уровень 2: Стандарт (Применение карт, Наложение статусов, Значения кубиков)
    VERBOSE = 3  # Уровень 3: Полный (Триггеры пассивок, Кулдауны, Детали расчетов, Начало фаз)


class BattleLogger:
    """
    Система логгирования.
    - Пишет ВСЕ логи в файл data/logs/full_battle_log.txt.
    - Сохраняет логи в st.session_state для отображения в UI с фильтрацией.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BattleLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Инициализация происходит один раз при создании
        if not hasattr(self, 'initialized'):
            self.ensure_log_dir()
            # При первом запуске (или перезагрузке сервера) можно отбить начало сессии
            # Но файл мы будем очищать только по команде clear(), чтобы сохранять историю между реранами
            self.initialized = True

    def ensure_log_dir(self):
        """Создает папку для логов, если её нет."""
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    def log(self, message: str, level: LogLevel = LogLevel.NORMAL, category: str = "Info"):
        """
        Основной метод записи лога.

        Args:
            message (str): Текст сообщения.
            level (LogLevel): Важность (MINIMAL, NORMAL, VERBOSE).
            category (str): Категория (Combat, Effect, System, Dice...).
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Часы:Минуты:Секунды.Миллисекунды

        # 1. Запись в файл (Пишем ВСЕГДА всё подряд для дебага)
        # Формат: [TIME] [LEVEL] [CATEGORY] Message
        log_entry_str = f"[{timestamp}] [{level.name:<7}] [{category}] {message}\n"

        try:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(log_entry_str)
        except Exception as e:
            print(f"Logger File Error: {e}")

        # 2. Запись в память (Session State) для UI
        session_state = _get_session_state()
        if session_state is None:
            storage = _memory_log_storage
        else:
            if 'battle_log_storage' not in session_state:
                session_state['battle_log_storage'] = []
            storage = session_state['battle_log_storage']

        # Сохраняем объект лога
        ui_entry = {
            "id": len(storage),
            "time": timestamp,
            "level": level,
            "category": category,
            "message": message
        }

        storage.append(ui_entry)

    def clear(self):
        """
        Очищает логи в памяти и перезаписывает файл (например, при кнопке Reset Battle).
        """
        session_state = _get_session_state()
        if session_state is None:
            _memory_log_storage.clear()
        else:
            session_state['battle_log_storage'] = []

        try:
            with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(f"=== BATTLE LOG CLEARED: {datetime.now()} ===\n")
        except Exception as e:
            print(f"Logger Clear Error: {e}")

    def get_logs_for_ui(self, filter_level: LogLevel):
        """
        Возвращает список логов для отображения, фильтруя по уровню.
        Пример: Если выбран NORMAL (2), покажет MINIMAL (1) и NORMAL (2).
        """
        session_state = _get_session_state()
        storage = _memory_log_storage if session_state is None else session_state.get('battle_log_storage', [])

        return [entry for entry in storage if entry['level'] <= filter_level]

    def get_logs(self):
        """
        Возвращает простой список сообщений (строк) из текущей сессии.
        Используется в профиле для отображения лога расчета.
        """
        session_state = _get_session_state()
        storage = _memory_log_storage if session_state is None else session_state.get('battle_log_storage', [])
        return [entry['message'] for entry in storage]


# Глобальный экземпляр логгера для импорта в других файлах
logger = BattleLogger()