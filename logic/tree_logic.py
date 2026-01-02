from logic.passives import PASSIVE_REGISTRY
from logic.talents import TALENT_REGISTRY

def get_talent_info(talent_id):
    return TALENT_REGISTRY.get(talent_id) or PASSIVE_REGISTRY.get(talent_id)

def count_branch_progress(unit, branch_key, skill_tree_data):
    """Считает количество изученных талантов в конкретной ветке."""
    if branch_key not in skill_tree_data: return 0

    nodes = skill_tree_data[branch_key]
    count = 0
    for node in nodes:
        tid = node["id"]
        if tid and (tid in unit.talents or tid in unit.passives):
            count += 1
    return count


def can_unlock_talent(unit, talent_node, skill_tree_data=None):  # Добавили аргумент
    tid = talent_node["id"]
    req = talent_node["req"]  # Для обычных талантов
    custom_req = talent_node.get("custom_req")  # НОВОЕ ПОЛЕ для Связей

    if not tid: return False, "WIP"
    if tid in unit.talents or tid in unit.passives: return False, "Already Learned"

    # --- ЛОГИКА СВЯЗЕЙ ---
    if custom_req and skill_tree_data:
        # custom_req = [("Ветка 4...", 5), ("Ветка 6...", 5)]
        for branch_name, needed_lvl in custom_req:
            # Ищем точный ключ ветки (по частичному совпадению или полному имени)
            # В tree_data ключи длинные ("Ветка 4: Медик..."), поэтому ищем совпадение
            real_key = next((k for k in skill_tree_data.keys() if branch_name in k), None)

            if not real_key:
                return False, f"Error: Branch {branch_name} not found"

            progress = count_branch_progress(unit, real_key, skill_tree_data)
            if progress < needed_lvl:
                return False, f"Нужно {needed_lvl} талантов в '{branch_name}' (Есть: {progress})"

        # Если все проверки прошли, проверяем очки талантов
        # (Оставим стандартную проверку ниже)

    # --- ОБЫЧНАЯ ЛОГИКА ---
    elif req:
        if req not in unit.talents and req not in unit.passives:
            parent = get_talent_info(req)
            p_name = parent.name if parent else req
            return False, f"Требуется: {p_name}"
    bonus_slots = 0
    if "talent_slots" in unit.modifiers:
        # В новой системе это словарь {'flat': X, 'pct': Y}
        bonus_slots = int(unit.modifiers["talent_slots"].get("flat", 0))

    max_slots = (unit.level // 3) + bonus_slots
    # Исключаем базовые пассивки
    spent = len([t for t in unit.talents if t != "base_passive"])

    if spent >= max_slots:
        return False, "Нет очков"

    return True, "Available"


def learn_talent(unit, talent_id):
    """Добавляет талант юниту."""
    # Определяем куда добавлять: в talents или passives
    # В вашей системе они разделены, но логика одна.
    # Проще всего всё кидать в unit.talents, если это активка/ветка,
    # но движок проверяет оба списка.

    if talent_id in TALENT_REGISTRY:
        unit.talents.append(talent_id)
        return True
    elif talent_id in PASSIVE_REGISTRY:
        unit.passives.append(talent_id)
        return True
    return False


def forget_talent(unit, talent_id):
    """Удаляет талант у юнита."""
    if talent_id in unit.talents:
        unit.talents.remove(talent_id)
        return True
    elif talent_id in unit.passives:
        unit.passives.remove(talent_id)
        return True
    return False


def can_forget_talent(unit, talent_id, skill_tree_data):
    """
    Проверяет, можно ли сбросить талант.
    Нельзя сбросить, если есть ИЗУЧЕННЫЕ таланты, которые требуют этот талант.
    """
    # Пробегаем по всему дереву
    for branch, nodes in skill_tree_data.items():
        for node in nodes:
            req = node.get("req")
            child_id = node.get("id")

            # Если этот узел требует наш талант...
            if req == talent_id:
                # ...и этот узел ИЗУЧЕН у юнита
                if child_id and (child_id in unit.talents or child_id in unit.passives):
                    child_obj = get_talent_info(child_id)
                    child_name = child_obj.name if child_obj else child_id
                    return False, f"Зависит: {child_name}"

    return True, "Можно сбросить"