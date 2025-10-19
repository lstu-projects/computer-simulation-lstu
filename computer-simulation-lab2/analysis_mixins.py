import numpy as np
from numpy.linalg import svd
import networkx as nx
import matplotlib.patches as mpatches


class AnalysisMixin:
    def analyze_network(self):
        """Проводит матричный анализ сети"""
        if not self.get_matrices_from_tables():
            return

        result_text = "=== МАТРИЧНЫЙ АНАЛИЗ СЕТИ ПЕТРИ ===\n\n"

        result_text += "Матрица входов F (описывает дуги от позиций к переходам):\n"
        result_text += "Каждый элемент F[p][t] показывает, сколько меток требуется из позиции p для срабатывания перехода t.\n"
        result_text += f"{str(self.F)}\n\n"

        result_text += "Матрица выходов H (описывает дуги от переходов к позициям):\n"
        result_text += "Каждый элемент H[t][p] показывает, сколько меток добавляется в позицию p после срабатывания перехода t.\n"
        result_text += f"{str(self.H)}\n\n"

        result_text += "Начальная разметка M0 (распределение меток в позициях на старте):\n"
        result_text += f"{self.M0}\n\n"

        result_text += "Матрица инцидентности C = H^T - F (изменение разметки при срабатывании переходов):\n"
        result_text += "Каждый столбец показывает вектор изменения разметки при срабатывании соответствующего перехода.\n"
        result_text += f"{str(self.C)}\n\n"

        result_text += "=== АНАЛИЗ ИНВАРИАНТОВ ===\n\n"
        result_text += "Инварианты - это свойства, которые остаются постоянными при эволюции сети.\n"
        result_text += (
            "P-инварианты помогают анализировать ограниченность, T-инварианты - циклы и живость.\n\n"
        )

        result_text += "Поиск P-инвариантов (решения уравнения y*C = 0, где y - вектор весов позиций):\n"
        result_text += "P-инвариант - это взвешенная сумма меток в позициях, которая не меняется.\n"
        try:
            u, s, vt = svd(self.C.T)
            null_mask = s <= 1e-5
            null_space = vt[len(s) :, :].T

            if null_space.size > 0:
                result_text += f"Найдено {null_space.shape[1]} P-инвариант(ов):\n"
                for i in range(null_space.shape[1]):
                    p_inv = null_space[:, i]
                    if np.any(p_inv < 0):
                        p_inv = -p_inv
                    p_inv = np.round(p_inv, decimals=3)
                    result_text += f"P-инвариант {i+1}: {p_inv}\n"

                    if np.all(p_inv > 1e-10):
                        result_text += "  -> Полный P-инвариант: сеть инвариантна (сумма меток постоянна).\n"
                    else:
                        result_text += "  -> Частичный P-инвариант: охватывает не все позиции.\n"
                result_text += "\n"
            else:
                result_text += "P-инвариантов не найдено. Сеть может быть неограниченной.\n\n"
        except Exception as e:
            result_text += f"Ошибка при поиске P-инвариантов: {str(e)}\n\n"

        result_text += (
            "Поиск T-инвариантов (решения уравнения C*x = 0, где x - вектор срабатываний переходов):\n"
        )
        result_text += (
            "T-инвариант - это последовательность срабатываний переходов, возвращающая разметку к исходной.\n"
        )
        try:
            u, s, vt = svd(self.C)
            null_mask = s <= 1e-5
            null_space = vt[len(s) :, :].T

            if null_space.size > 0:
                result_text += f"Найдено {null_space.shape[1]} T-инвариант(ов):\n"
                for i in range(null_space.shape[1]):
                    t_inv = null_space[:, i]
                    if np.any(t_inv < 0):
                        t_inv = -t_inv
                    t_inv = np.round(t_inv, decimals=3)
                    result_text += f"T-инвариант {i+1}: {t_inv}\n"

                    if np.all(t_inv > 1e-10):
                        result_text += "  -> Полный T-инвариант: сеть последовательная (имеет циклы охватывающие все переходы).\n"
                    else:
                        result_text += "  -> Частичный T-инвариант: охватывает не все переходы.\n"
                result_text += "\n"
            else:
                result_text += "T-инвариантов не найдено. Сеть может не иметь циклов.\n\n"
        except Exception as e:
            result_text += f"Ошибка при поиске T-инвариантов: {str(e)}\n\n"

        result_text += "=== АНАЛИЗ СВОЙСТВ СЕТИ ===\n\n"
        result_text += "На основе матричного анализа:\n"

        enabled_transitions = []
        for t in range(len(self.H)):
            enabled = True
            for p in range(len(self.F)):
                if self.M0[p] < self.F[p][t]:
                    enabled = False
                    break
            if enabled:
                enabled_transitions.append(t)

        result_text += f"Разрешенные переходы в M0 (переходы, которые могут сработать сразу): {[f'T{t+1}' for t in enabled_transitions]}\n\n"

        result_text += "ЗАКЛЮЧЕНИЕ:\n"
        result_text += "- P-инварианты указывают на сохранение ресурсов (меток).\n"
        result_text += "- T-инварианты указывают на циклы и воспроизводимость состояний.\n"
        result_text += "- Для полного анализа живости, безопасности и отсутствия тупиков необходимо\n"
        result_text += "  построить дерево достижимых разметок на соответствующей вкладке.\n"
        result_text += (
            "- Матричный анализ показывает структурные свойства сети, независимые от начальной разметки.\n"
        )

        self.matrix_results.setText(result_text)

    def build_and_visualize_reachability_tree(self):
        """Строит и визуализирует дерево достижимых разметок"""
        if not self.get_matrices_from_tables():
            return

        result_text, markings, tree_edges = self.build_reachability_tree_text()
        self.tree_results.setText(result_text)

        self.visualize_reachability_graph(markings, tree_edges)

    def build_reachability_tree_text(self):
        result_text = "=== ДЕРЕВО ДОСТИЖИМЫХ РАЗМЕТОК ===\n\n"

        markings = [self.M0.copy()]
        tree_edges = []
        processed = [False]

        omega = float("inf")

        result_text += f"Начальная разметка M0: {self.M0}\n\n"

        queue = [0]
        step = 0

        while queue and step < 50:
            step += 1
            current_idx = queue.pop(0)
            current_marking = markings[current_idx]

            result_text += f"Шаг {step}: Обрабатываем разметку M{current_idx}: {current_marking}\n"

            is_duplicate = False
            for i, existing_marking in enumerate(markings):
                if i != current_idx and np.array_equal(existing_marking, current_marking):
                    result_text += f"  -> Дублирует M{i}\n"
                    is_duplicate = True
                    break

            if is_duplicate:
                processed[current_idx] = True
                continue

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

                for p in range(len(new_marking)):
                    if new_marking[p] != omega:
                        new_marking[p] = new_marking[p] - self.F[p][t] + self.H[t][p]

                    if (
                        new_marking[p] > current_marking[p]
                        and current_marking[p] != omega
                        and new_marking[p] > 10
                    ):
                        new_marking[p] = omega

                existing_idx = -1
                for i, existing_marking in enumerate(markings):
                    if np.array_equal(existing_marking, new_marking):
                        existing_idx = i
                        break

                if existing_idx == -1:
                    markings.append(new_marking)
                    processed.append(False)
                    new_idx = len(markings) - 1
                    tree_edges.append((current_idx, new_idx, t))
                    queue.append(new_idx)

                    result_text += f"    T{t+1} -> M{new_idx}: {new_marking}\n"
                else:
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

        return result_text, markings, tree_edges

    def visualize_reachability_graph(self, markings, tree_edges):
        """Визуализирует граф дерева достижимости с прямоугольниками для переходов"""
        self.tree_figure.clear()
        ax = self.tree_figure.add_subplot(111)
        self.tree_figure.subplots_adjust(left=0.05, right=0.75, top=0.95, bottom=0.05)

        G = nx.DiGraph()

        for i, marking in enumerate(markings):
            marking_str = str(marking).replace("inf", "ω")
            G.add_node(i, label=f"M{i}: {marking_str}", node_type="marking")

        for from_idx, to_idx, t in tree_edges:
            transition_label = f"T{t+1}"
            G.add_node(transition_label, node_type="transition")
            G.add_edge(from_idx, transition_label)
            G.add_edge(transition_label, to_idx)

        pos = nx.spring_layout(G)

        marking_nodes = [n for n, attr in G.nodes(data=True) if attr["node_type"] == "marking"]
        nx.draw_networkx_nodes(
            G, pos, nodelist=marking_nodes, node_color="lightblue", node_shape="o", node_size=500, ax=ax
        )

        transition_nodes = [n for n, attr in G.nodes(data=True) if attr["node_type"] == "transition"]
        for t_node in transition_nodes:
            x, y = pos[t_node]
            rect = mpatches.Rectangle(
                (x - 0.2, y - 0.1),
                0.4,
                0.2,
                linewidth=1,
                edgecolor="black",
                facecolor="lightcoral",
                label="Переход" if t_node == transition_nodes[0] else "",
            )
            ax.add_patch(rect)
            ax.text(x, y, t_node, ha="center", va="center", fontsize=8, fontweight="bold", color="black")

        nx.draw_networkx_edges(G, pos, arrows=True, ax=ax)

        marking_labels = {n: G.nodes[n]["label"] for n in marking_nodes}
        nx.draw_networkx_labels(G, pos, labels=marking_labels, font_size=8, ax=ax)

        ax.set_title("Граф дерева достижимости")
        ax.axis("off")

        legend_elements = [
            mpatches.Circle((0, 0), 0.1, color="lightblue", label="Разметка"),
            mpatches.Rectangle(
                (0, 0), 0.4, 0.2, linewidth=1, edgecolor="black", facecolor="lightcoral", label="Переход"
            ),
        ]
        ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1.05, 1), borderaxespad=0.0)

        self.tree_canvas.draw()
