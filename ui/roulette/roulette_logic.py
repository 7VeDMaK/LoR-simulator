import random
from typing import Any, List, Dict, Callable, Optional


class RouletteRandomizer:
    """Рандомайзер для рулетки Рейна"""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Инициализация рандомайзера
        
        Args:
            seed: Начальное значение для генератора случайных чисел
        """
        self.rng = random.Random(seed)
        self.history: List[Any] = []
    
    def spin(self, items: List[Any], weights: Optional[List[float]] = None) -> Any:
        """
        Крутит рулетку и выбирает случайный элемент
        
        Args:
            items: Список элементов для выбора
            weights: Веса для каждого элемента (необязательно)
        
        Returns:
            Выбранный элемент
        """
        if not items:
            raise ValueError("Список элементов пуст")
        
        if weights:
            if len(weights) != len(items):
                raise ValueError("Количество весов должно совпадать с количеством элементов")
            result = self.rng.choices(items, weights=weights, k=1)[0]
        else:
            result = self.rng.choice(items)
        
        self.history.append(result)
        return result
    
    def spin_weighted(self, items_dict: Dict[Any, float]) -> Any:
        """
        Крутит рулетку с весами в виде словаря
        
        Args:
            items_dict: Словарь {элемент: вес}
        
        Returns:
            Выбранный элемент
        """
        items = list(items_dict.keys())
        weights = list(items_dict.values())
        return self.spin(items, weights)
    
    def multi_spin(self, items: List[Any], count: int, 
                   weights: Optional[List[float]] = None,
                   unique: bool = False) -> List[Any]:
        """
        Крутит рулетку несколько раз
        
        Args:
            items: Список элементов для выбора
            count: Количество кручений
            weights: Веса для каждого элемента (необязательно)
            unique: Если True, элементы не повторяются
        
        Returns:
            Список выбранных элементов
        """
        if unique and count > len(items):
            raise ValueError("Количество уникальных элементов больше доступных")
        
        results = []
        available_items = items.copy()
        available_weights = weights.copy() if weights else None
        
        for _ in range(count):
            if unique and available_weights:
                result = self.rng.choices(available_items, weights=available_weights, k=1)[0]
                idx = available_items.index(result)
                available_items.pop(idx)
                available_weights.pop(idx)
            elif unique:
                result = self.rng.choice(available_items)
                available_items.remove(result)
            elif available_weights:
                result = self.rng.choices(available_items, weights=available_weights, k=1)[0]
            else:
                result = self.rng.choice(available_items)
            
            results.append(result)
            self.history.append(result)
        
        return results
    
    def get_history(self, last_n: Optional[int] = None) -> List[Any]:
        """
        Возвращает историю выпавших элементов
        
        Args:
            last_n: Количество последних элементов (все, если None)
        
        Returns:
            Список элементов из истории
        """
        if last_n is None:
            return self.history.copy()
        return self.history[-last_n:]
    
    def clear_history(self):
        """Очищает историю"""
        self.history.clear()
    
    def reset_seed(self, seed: Optional[int] = None):
        """
        Сбрасывает генератор с новым seed
        
        Args:
            seed: Новое начальное значение
        """
        self.rng = random.Random(seed)
