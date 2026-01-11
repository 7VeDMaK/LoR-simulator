# ui/format_utils.py

def format_large_number(value) -> str:
    """
    Форматирует большие числа с суффиксами к/М/Б.
    Показывает до 2 знаков после запятой, убирая лишние нули.
    Примеры:
      1500 -> 1.5к
      1 050 000 000 -> 1.05Б
      1 000 000 -> 1М
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)

    # Меньше 1000 — показываем как целое
    if abs(val) < 1_000:
        return f"{int(val)}"

    suffix = ""
    divisor = 1

    if abs(val) >= 1_000_000_000:
        suffix = "Б"
        divisor = 1_000_000_000
    elif abs(val) >= 1_000_000:
        suffix = "М"
        divisor = 1_000_000
    else:
        suffix = "к"
        divisor = 1_000

    short_val = val / divisor

    # Форматируем с 2 знаками после запятой
    formatted = f"{short_val:.2f}"

    # Убираем лишние нули и точку в конце (1.50 -> 1.5; 1.00 -> 1)
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")

    return f"{formatted}{suffix}"