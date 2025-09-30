import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


class VisualizationMixin:
    def visualize_network(
        self,
        highlight_transition=None,
        highlight_color="red",
        input_frac=None,
        output_frac=None,
        old_marking=None,
    ):
        """Визуализирует сеть Петри с анимацией"""
        if not self.get_matrices_from_tables():
            return

        if input_frac is None:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            self.figure.subplots_adjust(left=0.05, right=0.75, top=0.95, bottom=0.05)
        else:
            ax = self.figure.axes[0]
            ax.clear()

        G = nx.DiGraph()

        display_marking = self.current_marking if self.current_marking is not None else self.M0

        positions_labels = [f"P{i+1}" for i in range(len(display_marking))]
        transitions_labels = [f"T{i+1}" for i in range(self.H.shape[0])]

        G.add_nodes_from(positions_labels)
        G.add_nodes_from(transitions_labels)

        for p in range(len(positions_labels)):
            for t in range(len(transitions_labels)):
                if self.F[p][t] > 0:
                    G.add_edge(positions_labels[p], transitions_labels[t], weight=self.F[p][t], type="input")
                if self.H[t][p] > 0:
                    G.add_edge(transitions_labels[t], positions_labels[p], weight=self.H[t][p], type="output")

        pos_nodes = [n for n in G.nodes() if n.startswith("P")]
        pos = nx.bipartite_layout(G, pos_nodes, scale=2)

        enabled_transitions = self.get_enabled_transitions()

        nx.draw_networkx_nodes(
            G, pos, nodelist=pos_nodes, node_color="lightblue", node_shape="o", node_size=2000, ax=ax
        )

        normal_transitions = [f"T{i+1}" for i in range(self.H.shape[0]) if i != highlight_transition]
        if normal_transitions:
            nx.draw_networkx_nodes(
                G,
                pos,
                nodelist=normal_transitions,
                node_color="lightcoral",
                node_shape="s",
                node_size=1500,
                ax=ax,
            )

        if highlight_transition is not None:
            highlight_node = [f"T{highlight_transition+1}"]
            if isinstance(highlight_color, tuple):
                node_color = [highlight_color]
            else:
                node_color = highlight_color
            nx.draw_networkx_nodes(
                G, pos, nodelist=highlight_node, node_color=node_color, node_shape="s", node_size=1500, ax=ax
            )

        enabled_nodes = [f"T{i+1}" for i in enabled_transitions if i != highlight_transition]
        if enabled_nodes:
            nx.draw_networkx_nodes(
                G, pos, nodelist=enabled_nodes, node_color="lightgreen", node_shape="s", node_size=1500, ax=ax
            )

        nx.draw_networkx_edges(G, pos, ax=ax, edge_color="gray", arrows=True, arrowsize=20, arrowstyle="->")

        nx.draw_networkx_labels(G, pos, ax=ax, font_size=10, font_weight="bold")

        marking_to_draw = old_marking if old_marking is not None else display_marking
        for i, p_label in enumerate(positions_labels):
            if input_frac is not None and highlight_transition is not None:
                is_input = self.F[i][highlight_transition] > 0
                is_output = self.H[highlight_transition][i] > 0
                tokens = marking_to_draw[i]
                if is_input:
                    tokens = marking_to_draw[i] if input_frac < 1 else display_marking[i]
                if is_output:
                    tokens = display_marking[i] if output_frac > 0 else marking_to_draw[i]
            else:
                tokens = display_marking[i]

            if tokens > 0:
                self.draw_tokens(ax, pos[p_label], tokens)

        if input_frac is not None and highlight_transition is not None:
            t_label = transitions_labels[highlight_transition]
            t_pos = pos[t_label]

            if input_frac < 1:
                for p_idx in range(len(positions_labels)):
                    weight = self.F[p_idx][highlight_transition]
                    p_label = positions_labels[p_idx]
                    p_pos = pos[p_label]
                    for _ in range(weight):
                        token_pos = (1 - input_frac) * np.array(p_pos) + input_frac * np.array(t_pos)
                        circle = patches.Circle(token_pos, 0.05, color="black")
                        ax.add_patch(circle)

            if output_frac > 0:
                for p_idx in range(len(positions_labels)):
                    weight = self.H[highlight_transition][p_idx]
                    p_label = positions_labels[p_idx]
                    p_pos = pos[p_label]
                    for _ in range(weight):
                        token_pos = (1 - output_frac) * np.array(t_pos) + output_frac * np.array(p_pos)
                        circle = patches.Circle(token_pos, 0.05, color="black")
                        ax.add_patch(circle)

        edge_labels = {}
        for p in range(len(positions_labels)):
            for t in range(len(transitions_labels)):
                if self.F[p][t] > 1:
                    edge_labels[(positions_labels[p], transitions_labels[t])] = str(self.F[p][t])
                if self.H[t][p] > 1:
                    edge_labels[(transitions_labels[t], positions_labels[p])] = str(self.H[t][p])

        if edge_labels:
            nx.draw_networkx_edge_labels(G, pos, edge_labels, ax=ax, font_size=8)

        ax.set_title("Визуализация сети Петри", fontsize=14, fontweight="bold")
        ax.axis("off")

        legend_elements = [
            plt.Line2D(
                [0], [0], marker="o", color="w", markerfacecolor="lightblue", markersize=15, label="Позиция"
            ),
            plt.Line2D(
                [0], [0], marker="s", color="w", markerfacecolor="lightcoral", markersize=12, label="Переход"
            ),
            plt.Line2D(
                [0],
                [0],
                marker="s",
                color="w",
                markerfacecolor="lightgreen",
                markersize=12,
                label="Разрешенный переход",
            ),
            plt.Line2D(
                [0],
                [0],
                marker="s",
                color="w",
                markerfacecolor="red",
                markersize=12,
                label="Срабатывающий переход",
            ),
        ]
        ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1.05, 1), borderaxespad=0.0)

        self.canvas.draw()

    def draw_tokens(self, ax, position, num_tokens):
        """Рисует метки в позиции"""
        if num_tokens == 1:
            circle = patches.Circle(position, 0.1, color="black")
            ax.add_patch(circle)
        elif num_tokens <= 5:
            for i in range(num_tokens):
                angle = 2 * np.pi * i / num_tokens
                x = position[0] + 0.15 * np.cos(angle)
                y = position[1] + 0.15 * np.sin(angle)
                circle = patches.Circle((x, y), 0.05, color="black")
                ax.add_patch(circle)
        else:
            ax.text(
                position[0],
                position[1],
                str(num_tokens),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color="black",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="black"),
            )
