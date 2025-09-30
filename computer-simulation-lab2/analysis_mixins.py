import numpy as np
from scipy.linalg import svd


class AnalysisMixin:
    def analyze_network(self):
        """Проводит матричный анализ сети"""
        if not self.get_matrices_from_tables():
            return

        result_text = "=== МАТРИЧНЫЙ АНАЛИЗ СЕТИ ПЕТРИ ===\n\n"

        result_text += f"Матрица входов F ({self.F.shape[0]}×{self.F.shape[1]}):\n"
        result_text += str(self.F) + "\n\n"

        result_text += f"Матрица выходов H ({self.H.shape[0]}×{self.H.shape[1]}):\n"
        result_text += str(self.H) + "\n\n"

        result_text += f"Начальная разметка M0:\n{self.M0}\n\n"

        result_text += f"Матрица инцидентности C = H^T - F:\n"
        result_text += str(self.C) + "\n\n"

        result_text += "=== АНАЛИЗ ИНВАРИАНТОВ ===\n\n"

        # P-инварианты (решения y*C = 0)
        result_text += "Поиск P-инвариантов (решения уравнения y*C = 0):\n"
        try:
            # нулевое пространство C^T
            u, s, vt = svd(self.C.T)
            null_mask = s <= 1e-10
            null_space = vt[len(s) :, :].T

            if null_space.size > 0:
                result_text += f"Найдено {null_space.shape[1]} P-инвариант(ов):\n"
                for i in range(null_space.shape[1]):
                    p_inv = null_space[:, i]
                    # Нормализуем, чтобы избежать отрицательных значений
                    if np.any(p_inv < 0):
                        p_inv = -p_inv
                    result_text += f"P-инвариант {i+1}: {p_inv}\n"

                    # Проверяем на полноту (все элементы > 0)
                    if np.all(p_inv > 1e-10):
                        result_text += "  -> Полный P-инвариант (сеть инвариантная)\n"
                result_text += "\n"
            else:
                result_text += "P-инвариантов не найдено\n\n"
        except Exception as e:
            result_text += f"Ошибка при поиске P-инвариантов: {str(e)}\n\n"

        # T-инварианты (решения C*x = 0)
        result_text += "Поиск T-инвариантов (решения уравнения C*x = 0):\n"
        try:
            u, s, vt = svd(self.C)
            null_mask = s <= 1e-10
            null_space = vt[len(s) :, :].T

            if null_space.size > 0:
                result_text += f"Найдено {null_space.shape[1]} T-инвариант(ов):\n"
                for i in range(null_space.shape[1]):
                    t_inv = null_space[:, i]
                    # Нормализуем, чтобы избежать отрицательных значений
                    if np.any(t_inv < 0):
                        t_inv = -t_inv
                    result_text += f"T-инвариант {i+1}: {t_inv}\n"

                    # Проверяем на полноту (все элементы > 0)
                    if np.all(t_inv > 1e-10):
                        result_text += "  -> Полный T-инвариант (сеть последовательная)\n"
                result_text += "\n"
            else:
                result_text += "T-инвариантов не найдено\n\n"
        except Exception as e:
            result_text += f"Ошибка при поиске T-инвариантов: {str(e)}\n\n"

        result_text += "=== АНАЛИЗ СВОЙСТВ СЕТИ ===\n\n"

        enabled_transitions = []
        for t in range(len(self.H)):
            enabled = True
            for p in range(len(self.F)):
                if self.M0[p] < self.F[p][t]:
                    enabled = False
                    break
            if enabled:
                enabled_transitions.append(t)

        result_text += f"Разрешенные переходы в M0: {[f'T{t+1}' for t in enabled_transitions]}\n\n"

        result_text += "ЗАКЛЮЧЕНИЕ:\n"
        result_text += "- Для полного анализа живости и безопасности необходимо\n"
        result_text += "  построить дерево достижимых разметок\n"
        result_text += "- Матричный анализ показывает структурные свойства сети\n"

        self.matrix_results.setText(result_text)

    def build_reachability_tree(self):
        """Строит дерево достижимых разметок"""
        if not self.get_matrices_from_tables():
            return

        result_text = "=== ДЕРЕВО ДОСТИЖИМЫХ РАЗМЕТОК ===\n\n"

        # Структуры для хранения дерева
        markings = [self.M0.copy()]  # Список всех разметок
        tree_edges = []  # Ребра дерева (индекс_от, индекс_к, переход)
        processed = [False]  # Обработанные вершины

        omega = float("inf")

        result_text += f"Начальная разметка M0: {self.M0}\n\n"

        # Алгоритм построения дерева
        queue = [0]  # Очередь необработанных вершин (индексы)
        step = 0

        while queue and step < 50:
            step += 1
            current_idx = queue.pop(0)
            current_marking = markings[current_idx]

            result_text += f"Шаг {step}: Обрабатываем разметку M{current_idx}: {current_marking}\n"

            # Проверяем, является ли разметка дублирующей
            is_duplicate = False
            for i, existing_marking in enumerate(markings):
                if i != current_idx and np.array_equal(existing_marking, current_marking):
                    result_text += f"  -> Дублирует M{i}\n"
                    is_duplicate = True
                    break

            if is_duplicate:
                processed[current_idx] = True
                continue

            # Находим разрешенные переходы
            enabled_transitions = []
            for t in range(self.H.shape[0]):
                enabled = True
                for p in range(len(current_marking)):
                    if current_marking[p] != omega and current_marking[p] < self.F[p][t]:
                        enabled = False
                        break
                if enabled:
                    enabled_transitions.append(t)

            if not enabled_transitions:
                result_text += "  -> Тупиковая разметка\n"
                processed[current_idx] = True
                continue

            result_text += f"  -> Разрешенные переходы: {[f'T{t+1}' for t in enabled_transitions]}\n"

            for t in enabled_transitions:
                new_marking = current_marking.copy()

                # Применяем правило срабатывания перехода
                for p in range(len(new_marking)):
                    if new_marking[p] != omega:
                        new_marking[p] = new_marking[p] - self.F[p][t] + self.H[t][p]

                    # Проверяем условие ω
                    # Если новое значение больше предыдущего и есть путь с возрастающей последовательностью
                    if (
                        new_marking[p] > current_marking[p]
                        and current_marking[p] != omega
                        and new_marking[p] > 10
                    ):  # Упрощенное условие
                        new_marking[p] = omega

                # Проверяем, существует ли уже такая разметка
                existing_idx = -1
                for i, existing_marking in enumerate(markings):
                    if np.array_equal(existing_marking, new_marking):
                        existing_idx = i
                        break

                if existing_idx == -1:
                    # Добавляем новую разметку
                    markings.append(new_marking)
                    processed.append(False)
                    new_idx = len(markings) - 1
                    tree_edges.append((current_idx, new_idx, t))
                    queue.append(new_idx)

                    result_text += f"    T{t+1} -> M{new_idx}: {new_marking}\n"
                else:
                    # Ссылаемся на существующую разметку
                    tree_edges.append((current_idx, existing_idx, t))
                    result_text += f"    T{t+1} -> M{existing_idx} (существующая)\n"

            processed[current_idx] = True
            result_text += "\n"

        result_text += "\n=== АНАЛИЗ СВОЙСТВ НА ОСНОВЕ ДЕРЕВА ===\n\n"

        is_safe = True
        is_bounded = True
        max_tokens = 0

        for i, marking in enumerate(markings):
            for tokens in marking:
                if tokens == omega:
                    is_bounded = False
                    is_safe = False
                elif tokens > 1:
                    is_safe = False
                if tokens != omega and tokens > max_tokens:
                    max_tokens = tokens

        result_text += f"Безопасность: {'ДА' if is_safe else 'НЕТ'}\n"
        result_text += f"Ограниченность: {'ДА' if is_bounded else 'НЕТ'}\n"
        if is_bounded:
            result_text += f"Максимальное количество меток: {max_tokens}\n"
        result_text += "\n"

        reachable_transitions = set()
        for _, _, transition in tree_edges:
            reachable_transitions.add(transition)

        all_transitions = set(range(self.H.shape[0]))
        unreachable = all_transitions - reachable_transitions

        result_text += f"Достижимые переходы: {[f'T{t+1}' for t in sorted(reachable_transitions)]}\n"
        if unreachable:
            result_text += f"Недостижимые переходы: {[f'T{t+1}' for t in sorted(unreachable)]}\n"
            result_text += "Сеть НЕ является живой\n"
        else:
            result_text += "Все переходы достижимы (необходимое условие живости)\n"

        result_text += f"\nВсего найдено разметок: {len(markings)}\n"
        result_text += f"Ребер в дереве: {len(tree_edges)}\n"

        self.tree_results.setText(result_text)
