import pygame
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Tuple


class CellState(IntEnum):
    EMPTY = 0
    TREE = 1
    BURNING = 2


class NeighborhoodType(IntEnum):
    VON_NEUMANN = 0  # 4 соседа
    MOORE = 1  # 8 соседей


@dataclass
class SimulationParams:
    rows: int
    cols: int
    initial_tree_percent: float
    initial_burning_percent: float
    generations: int
    neighborhood: NeighborhoodType
    deterministic: bool
    grow_probability: float = 1.0
    spontaneous_fire_probability: float = 0.0
    use_age: bool = False
    max_age: int = 100


@dataclass
class Statistics:
    generation: int
    alive_trees: int
    burning_trees: int
    empty_cells: int
    trees_grown: int
    trees_ignited: int
    trees_died: int
    forest_density: float
    max_age: int
    avg_age: float


class ForestFireSimulation:
    def __init__(self, params: SimulationParams):
        self.params = params
        self.grid = np.zeros((params.rows, params.cols), dtype=int)
        self.ages = np.zeros((params.rows, params.cols), dtype=int)
        self.generation = 0
        self.statistics: List[Statistics] = []
        self.max_age_ever = 0
        self.total_trees_grown = 0
        self.total_trees_died = 0
        self.total_fires = 0
        self.initialize_grid()

    def initialize_grid(self):
        """Инициализация начальной сетки"""
        total_cells = self.params.rows * self.params.cols

        num_trees = int(total_cells * self.params.initial_tree_percent)
        tree_positions = np.random.choice(total_cells, num_trees, replace=False)

        for pos in tree_positions:
            row, col = pos // self.params.cols, pos % self.params.cols
            self.grid[row, col] = CellState.TREE
            if self.params.use_age:
                self.ages[row, col] = np.random.randint(1, self.params.max_age // 2)

        num_burning = int(num_trees * self.params.initial_burning_percent)
        if num_burning > 0:
            burning_indices = np.random.choice(len(tree_positions), num_burning, replace=False)
            for idx in burning_indices:
                pos = tree_positions[idx]
                row, col = pos // self.params.cols, pos % self.params.cols
                self.grid[row, col] = CellState.BURNING

    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Получить координаты соседей"""
        neighbors = []

        if self.params.neighborhood == NeighborhoodType.VON_NEUMANN:
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        else:
            deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        for dr, dc in deltas:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.params.rows and 0 <= nc < self.params.cols:
                neighbors.append((nr, nc))

        return neighbors

    def has_burning_neighbor(self, row: int, col: int) -> bool:
        """Проверить, есть ли горящие соседи"""
        neighbors = self.get_neighbors(row, col)
        for nr, nc in neighbors:
            if self.grid[nr, nc] == CellState.BURNING:
                return True
        return False

    def update(self):
        """Обновить состояние сетки на одно поколение"""
        new_grid = self.grid.copy()
        new_ages = self.ages.copy()

        trees_grown = 0
        trees_ignited = 0
        trees_died = 0

        for row in range(self.params.rows):
            for col in range(self.params.cols):
                current_state = self.grid[row, col]

                if current_state == CellState.BURNING:
                    new_grid[row, col] = CellState.EMPTY
                    new_ages[row, col] = 0
                    trees_died += 1

                elif current_state == CellState.TREE:
                    if self.has_burning_neighbor(row, col):
                        new_grid[row, col] = CellState.BURNING
                        new_ages[row, col] = 0
                        trees_ignited += 1
                    else:
                        if self.params.use_age:
                            new_ages[row, col] += 1
                            if new_ages[row, col] >= self.params.max_age:
                                new_grid[row, col] = CellState.EMPTY
                                new_ages[row, col] = 0
                                trees_died += 1

                elif current_state == CellState.EMPTY:
                    if not self.has_burning_neighbor(row, col):
                        if self.params.deterministic:
                            new_grid[row, col] = CellState.TREE
                            new_ages[row, col] = 1
                            trees_grown += 1
                        else:
                            if np.random.random() < self.params.grow_probability:
                                new_grid[row, col] = CellState.TREE
                                new_ages[row, col] = 1
                                trees_grown += 1

        if not self.params.deterministic:
            for row in range(self.params.rows):
                for col in range(self.params.cols):
                    if new_grid[row, col] == CellState.TREE:
                        if np.random.random() < self.params.spontaneous_fire_probability:
                            new_grid[row, col] = CellState.BURNING
                            new_ages[row, col] = 0
                            trees_ignited += 1

        self.grid = new_grid
        self.ages = new_ages
        self.generation += 1

        self.total_trees_grown += trees_grown
        self.total_trees_died += trees_died
        if trees_ignited > 0:
            self.total_fires += 1

        alive_trees = np.sum(self.grid == CellState.TREE)
        burning_trees = np.sum(self.grid == CellState.BURNING)
        empty_cells = np.sum(self.grid == CellState.EMPTY)
        forest_density = alive_trees / (self.params.rows * self.params.cols)

        if self.params.use_age and alive_trees > 0:
            tree_ages = self.ages[self.grid == CellState.TREE]
            max_age = int(np.max(tree_ages))
            avg_age = float(np.mean(tree_ages))
            self.max_age_ever = max(self.max_age_ever, max_age)
        else:
            max_age = 0
            avg_age = 0.0

        stats = Statistics(
            generation=self.generation,
            alive_trees=int(alive_trees),
            burning_trees=int(burning_trees),
            empty_cells=int(empty_cells),
            trees_grown=trees_grown,
            trees_ignited=trees_ignited,
            trees_died=trees_died,
            forest_density=forest_density,
            max_age=max_age,
            avg_age=avg_age,
        )

        self.statistics.append(stats)
        return stats


class Button:
    def __init__(self, x, y, width, height, text, color=(70, 130, 180), hover_color=(100, 160, 210)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=8)

        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False


class InputField:
    def __init__(self, x, y, width, height, label, default_value, value_type=str):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = str(default_value)
        self.default_value = default_value
        self.value_type = value_type
        self.active = False

    def draw(self, screen, font, small_font):
        label_surf = small_font.render(self.label, True, (220, 220, 220))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 22))

        color = (100, 150, 200) if self.active else (60, 60, 70)
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        pygame.draw.rect(
            screen, (255, 255, 255) if self.active else (150, 150, 150), self.rect, 2, border_radius=4
        )

        text_surf = font.render(self.value, True, (255, 255, 255))
        screen.blit(text_surf, (self.rect.x + 8, self.rect.y + 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            else:
                self.value += event.unicode

    def get_value(self):
        try:
            if self.value_type == int:
                return int(self.value)
            elif self.value_type == float:
                return float(self.value)
            elif self.value_type == bool:
                return self.value.lower() in ["true", "1", "yes", "y"]
            return self.value
        except:
            return self.default_value


class Checkbox:
    def __init__(self, x, y, label, default_value=False):
        self.rect = pygame.Rect(x, y, 22, 22)
        self.label = label
        self.checked = default_value

    def draw(self, screen, font):
        pygame.draw.rect(screen, (60, 60, 70), self.rect, border_radius=4)
        pygame.draw.rect(
            screen, (255, 255, 255) if self.checked else (150, 150, 150), self.rect, 2, border_radius=4
        )

        if self.checked:
            pygame.draw.line(
                screen,
                (50, 205, 50),
                (self.rect.x + 4, self.rect.y + 11),
                (self.rect.x + 9, self.rect.y + 16),
                3,
            )
            pygame.draw.line(
                screen,
                (50, 205, 50),
                (self.rect.x + 9, self.rect.y + 16),
                (self.rect.x + 18, self.rect.y + 6),
                3,
            )

        label_surf = font.render(self.label, True, (220, 220, 220))
        screen.blit(label_surf, (self.rect.x + 32, self.rect.y + 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                return True
        return False


class MenuScreen:
    def __init__(self, width=1200, height=800):
        pygame.init()

        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Симуляция: Лесной пожар")

        self.font = pygame.font.Font(None, 48)
        self.medium_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 22)

        self.setup_ui()

    def setup_ui(self):
        button_width = 350
        button_height = 70
        center_x = self.width // 2 - button_width // 2
        start_y = 250

        self.start_button = Button(
            center_x,
            start_y,
            button_width,
            button_height,
            "Запустить симуляцию",
            (50, 150, 50),
            (70, 180, 70),
        )
        self.experiment_button = Button(
            center_x,
            start_y + 90,
            button_width,
            button_height,
            "Запустить эксперименты",
            (70, 130, 180),
            (100, 160, 210),
        )
        self.quit_button = Button(
            center_x, start_y + 180, button_width, button_height, "Выход", (180, 70, 70), (210, 100, 100)
        )

    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            for i in range(self.height):
                color_value = int(20 + (i / self.height) * 15)
                pygame.draw.line(
                    self.screen, (color_value, color_value, color_value + 10), (0, i), (self.width, i)
                )

            title_text = "Симуляция 'Лесной пожар'"
            shadow = self.font.render(title_text, True, (0, 0, 0))
            title = self.font.render(title_text, True, (255, 200, 100))

            title_rect = title.get_rect(center=(self.width // 2, 120))
            shadow_rect = shadow.get_rect(center=(self.width // 2 + 3, 123))

            self.screen.blit(shadow, shadow_rect)
            self.screen.blit(title, title_rect)

            subtitle = self.small_font.render(
                "Клеточный автомат с стохастическими правилами", True, (180, 180, 200)
            )
            subtitle_rect = subtitle.get_rect(center=(self.width // 2, 165))
            self.screen.blit(subtitle, subtitle_rect)

            self.start_button.draw(self.screen, self.medium_font)
            self.experiment_button.draw(self.screen, self.medium_font)
            self.quit_button.draw(self.screen, self.medium_font)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return None
                elif event.type == pygame.VIDEORESIZE:
                    self.width = event.w
                    self.height = event.h
                    self.setup_ui()

                if self.start_button.handle_event(event):
                    return "simulation"
                if self.experiment_button.handle_event(event):
                    return "experiments"
                if self.quit_button.handle_event(event):
                    return None

            pygame.display.flip()
            clock.tick(60)

        return None


class ParameterScreen:
    def __init__(self, width=1200, height=800):
        pygame.init()

        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Настройка параметров")

        self.font = pygame.font.Font(None, 40)
        self.medium_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

        self.setup_inputs()

    def setup_inputs(self):
        left_col_x = 120
        right_col_x = 620
        start_y = 140
        field_height = 32
        field_width = 220
        spacing = 65

        self.rows_input = InputField(
            left_col_x, start_y, field_width, field_height, "Количество строк:", 50, int
        )
        self.cols_input = InputField(
            left_col_x, start_y + spacing, field_width, field_height, "Количество столбцов:", 50, int
        )
        self.tree_percent_input = InputField(
            left_col_x,
            start_y + spacing * 2,
            field_width,
            field_height,
            "% живых деревьев (0-1):",
            0.6,
            float,
        )
        self.burning_percent_input = InputField(
            left_col_x,
            start_y + spacing * 3,
            field_width,
            field_height,
            "% горящих деревьев (0-1):",
            0.01,
            float,
        )
        self.generations_input = InputField(
            left_col_x, start_y + spacing * 4, field_width, field_height, "Число поколений:", 500, int
        )

        self.grow_prob_input = InputField(
            right_col_x, start_y, field_width, field_height, "Вероятность роста (0-1):", 0.1, float
        )
        self.fire_prob_input = InputField(
            right_col_x,
            start_y + spacing,
            field_width,
            field_height,
            "Вероятность возгорания (0-1):",
            0.0005,
            float,
        )
        self.max_age_input = InputField(
            right_col_x, start_y + spacing * 2, field_width, field_height, "Макс. возраст:", 100, int
        )

        checkbox_y = start_y + spacing * 3
        self.moore_checkbox = Checkbox(right_col_x, checkbox_y, "Окрестность Мура (иначе фон Нейман)", True)
        self.deterministic_checkbox = Checkbox(
            right_col_x, checkbox_y + 45, "Детерминированная модель", False
        )
        self.use_age_checkbox = Checkbox(right_col_x, checkbox_y + 90, "Учитывать возраст деревьев", False)

        button_width = 220
        button_height = 55
        button_y = self.height - 110

        self.start_button = Button(
            self.width // 2 - button_width - 15,
            button_y,
            button_width,
            button_height,
            "Запустить",
            (50, 150, 50),
        )
        self.back_button = Button(
            self.width // 2 + 15, button_y, button_width, button_height, "Назад", (180, 70, 70)
        )

        self.inputs = [
            self.rows_input,
            self.cols_input,
            self.tree_percent_input,
            self.burning_percent_input,
            self.generations_input,
            self.grow_prob_input,
            self.fire_prob_input,
            self.max_age_input,
        ]

        self.checkboxes = [self.moore_checkbox, self.deterministic_checkbox, self.use_age_checkbox]

    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            for i in range(self.height):
                color_value = int(20 + (i / self.height) * 15)
                pygame.draw.line(
                    self.screen, (color_value, color_value, color_value + 10), (0, i), (self.width, i)
                )

            title = self.font.render("Настройка параметров симуляции", True, (255, 200, 100))
            title_rect = title.get_rect(center=(self.width // 2, 60))
            self.screen.blit(title, title_rect)

            section_font = pygame.font.Font(None, 28)
            basic_title = section_font.render("Основные параметры", True, (150, 200, 255))
            self.screen.blit(basic_title, (100, 100))

            advanced_title = section_font.render("Дополнительные настройки", True, (150, 200, 255))
            self.screen.blit(advanced_title, (600, 100))

            for input_field in self.inputs:
                input_field.draw(self.screen, self.medium_font, self.small_font)

            for checkbox in self.checkboxes:
                checkbox.draw(self.screen, self.small_font)

            self.start_button.draw(self.screen, self.medium_font)
            self.back_button.draw(self.screen, self.medium_font)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.VIDEORESIZE:
                    self.width = event.w
                    self.height = event.h
                    self.setup_inputs()

                for input_field in self.inputs:
                    input_field.handle_event(event)

                for checkbox in self.checkboxes:
                    checkbox.handle_event(event)

                if self.start_button.handle_event(event):
                    params = SimulationParams(
                        rows=self.rows_input.get_value(),
                        cols=self.cols_input.get_value(),
                        initial_tree_percent=self.tree_percent_input.get_value(),
                        initial_burning_percent=self.burning_percent_input.get_value(),
                        generations=self.generations_input.get_value(),
                        neighborhood=(
                            NeighborhoodType.MOORE
                            if self.moore_checkbox.checked
                            else NeighborhoodType.VON_NEUMANN
                        ),
                        deterministic=self.deterministic_checkbox.checked,
                        grow_probability=self.grow_prob_input.get_value(),
                        spontaneous_fire_probability=self.fire_prob_input.get_value(),
                        use_age=self.use_age_checkbox.checked,
                        max_age=self.max_age_input.get_value(),
                    )
                    return params

                if self.back_button.handle_event(event):
                    return "back"

            pygame.display.flip()
            clock.tick(60)

        return None


class Visualization:
    def __init__(self, simulation: ForestFireSimulation, cell_size: int = 8):
        pygame.init()

        self.simulation = simulation
        self.cell_size = cell_size

        grid_width = simulation.params.cols * cell_size
        grid_height = simulation.params.rows * cell_size
        info_panel_width = 400
        legend_height = 300

        self.width = grid_width + info_panel_width
        self.height = max(grid_height, 600) + legend_height

        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Симуляция: Лесной пожар")

        self.colors = {
            CellState.EMPTY: (50, 50, 50),
            CellState.TREE: (34, 139, 34),
            CellState.BURNING: (255, 69, 0),
        }

        self.font = pygame.font.Font(None, 28)
        self.medium_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 20)

        self.running = True
        self.paused = False
        self.speed = 10
        self.grid_offset_y = 60

    def draw_grid(self):
        """Отрисовка сетки"""
        for row in range(self.simulation.params.rows):
            for col in range(self.simulation.params.cols):
                state = self.simulation.grid[row, col]
                color = self.colors[state]

                if state == CellState.TREE and self.simulation.params.use_age:
                    age = self.simulation.ages[row, col]
                    max_age = self.simulation.params.max_age
                    age_factor = min(age / max_age, 1.0)
                    color = (
                        int(34 + (10 - 34) * age_factor),
                        int(139 + (80 - 139) * age_factor),
                        int(34 + (10 - 34) * age_factor),
                    )

                x = col * self.cell_size
                y = row * self.cell_size + self.grid_offset_y
                pygame.draw.rect(self.screen, color, (x, y, self.cell_size, self.cell_size))

    def draw_info_panel(self):
        """Отрисовка информационной панели с улучшенной статистикой"""
        grid_width = self.simulation.params.cols * self.cell_size
        panel_x = grid_width + 25
        y_offset = self.grid_offset_y

        available_height = min(
            self.simulation.params.rows * self.cell_size + 20, self.height - self.grid_offset_y - 10
        )

        panel_bg = pygame.Rect(
            grid_width + 10, self.grid_offset_y - 10, min(380, self.width - grid_width - 20), available_height
        )
        pygame.draw.rect(self.screen, (30, 30, 40), panel_bg, border_radius=10)
        pygame.draw.rect(self.screen, (80, 80, 100), panel_bg, 2, border_radius=10)

        title = self.font.render("Статистика", True, (255, 200, 100))
        self.screen.blit(title, (panel_x, y_offset))
        y_offset += 45

        if self.simulation.statistics:
            stats = self.simulation.statistics[-1]
            total_cells = self.simulation.params.rows * self.simulation.params.cols

            progress = stats.generation / self.simulation.params.generations
            progress_text = self.medium_font.render(
                f"Поколение: {stats.generation}/{self.simulation.params.generations}", True, (220, 220, 220)
            )
            self.screen.blit(progress_text, (panel_x, y_offset))
            y_offset += 25

            bar_width = min(330, self.width - panel_x - 50)
            bar_height = 18
            bar_rect = pygame.Rect(panel_x, y_offset, bar_width, bar_height)
            pygame.draw.rect(self.screen, (50, 50, 60), bar_rect, border_radius=9)
            fill_rect = pygame.Rect(panel_x, y_offset, int(bar_width * progress), bar_height)
            pygame.draw.rect(self.screen, (50, 150, 255), fill_rect, border_radius=9)
            pygame.draw.rect(self.screen, (100, 100, 120), bar_rect, 2, border_radius=9)
            y_offset += 35

            pygame.draw.line(
                self.screen, (80, 80, 100), (panel_x, y_offset), (panel_x + bar_width, y_offset), 2
            )
            y_offset += 15

            state_title = self.medium_font.render("Текущее состояние:", True, (150, 200, 255))
            self.screen.blit(state_title, (panel_x, y_offset))
            y_offset += 28

            info_lines = [
                (
                    f"Живые деревья: {stats.alive_trees} ({stats.alive_trees/total_cells*100:.1f}%)",
                    (100, 200, 100),
                ),
                (
                    f"Горящие: {stats.burning_trees} ({stats.burning_trees/total_cells*100:.1f}%)",
                    (255, 120, 60),
                ),
                (f"Пустые: {stats.empty_cells} ({stats.empty_cells/total_cells*100:.1f}%)", (150, 150, 150)),
                ("", None),
                (f"Плотность леса: {stats.forest_density:.4f}", (255, 255, 100)),
            ]

            for line, color in info_lines:
                if y_offset + 24 > panel_bg.bottom - 10:
                    break
                if line:
                    text = self.small_font.render(line, True, color if color else (200, 200, 200))
                    self.screen.blit(text, (panel_x + 5, y_offset))
                y_offset += 24

            if y_offset + 15 < panel_bg.bottom - 10:
                pygame.draw.line(
                    self.screen, (80, 80, 100), (panel_x, y_offset), (panel_x + bar_width, y_offset), 2
                )
                y_offset += 15

            if y_offset + 28 < panel_bg.bottom - 10:
                dynamics_title = self.medium_font.render("За это поколение:", True, (150, 200, 255))
                self.screen.blit(dynamics_title, (panel_x, y_offset))
                y_offset += 28

                dynamics_lines = [
                    (f"  Выросло: {stats.trees_grown}", (100, 255, 100)),
                    (f"  Загорелось: {stats.trees_ignited}", (255, 100, 50)),
                    (f"  Умерло: {stats.trees_died}", (150, 150, 150)),
                ]

                for line, color in dynamics_lines:
                    if y_offset + 24 > panel_bg.bottom - 10:
                        break
                    text = self.small_font.render(line, True, color)
                    self.screen.blit(text, (panel_x + 5, y_offset))
                    y_offset += 24

            if y_offset + 15 < panel_bg.bottom - 10:
                pygame.draw.line(
                    self.screen, (80, 80, 100), (panel_x, y_offset), (panel_x + bar_width, y_offset), 2
                )
                y_offset += 15

            if y_offset + 28 < panel_bg.bottom - 10:
                total_title = self.medium_font.render("За всё время:", True, (150, 200, 255))
                self.screen.blit(total_title, (panel_x, y_offset))
                y_offset += 28

                total_lines = [
                    f"  Всего выросло: {self.simulation.total_trees_grown}",
                    f"  Всего сгорело: {self.simulation.total_trees_died}",
                    f"  Пожаров: {self.simulation.total_fires}",
                ]

                for line in total_lines:
                    if y_offset + 24 > panel_bg.bottom - 10:
                        break
                    text = self.small_font.render(line, True, (200, 200, 200))
                    self.screen.blit(text, (panel_x + 5, y_offset))
                    y_offset += 24

            if self.simulation.params.use_age and y_offset + 90 < panel_bg.bottom - 10:
                y_offset += 5
                pygame.draw.line(
                    self.screen, (80, 80, 100), (panel_x, y_offset), (panel_x + bar_width, y_offset), 2
                )
                y_offset += 15

                age_title = self.medium_font.render("Возраст деревьев:", True, (150, 200, 255))
                self.screen.blit(age_title, (panel_x, y_offset))
                y_offset += 28

                age_lines = [
                    f"  Макс. сейчас: {stats.max_age}",
                    f"  Средний: {stats.avg_age:.1f}",
                    f"  Рекорд: {self.simulation.max_age_ever}",
                ]

                for line in age_lines:
                    if y_offset + 24 > panel_bg.bottom - 10:
                        break
                    text = self.small_font.render(line, True, (200, 200, 200))
                    self.screen.blit(text, (panel_x + 5, y_offset))
                    y_offset += 24

    def draw_legend(self):
        """Рисуем улучшенную легенду внизу экрана"""
        grid_height = self.simulation.params.rows * self.cell_size + self.grid_offset_y

        available_space = self.height - grid_height - 15
        if available_space < 120:
            return

        legend_height = min(270, available_space - 20)
        legend_y = grid_height + 50
        legend_x = 30

        pygame.draw.line(
            self.screen, (100, 100, 120), (0, grid_height + 15), (self.width, grid_height + 15), 3
        )

        legend_bg = pygame.Rect(legend_x - 15, legend_y - 15, self.width - 60, legend_height)
        pygame.draw.rect(self.screen, (30, 30, 40), legend_bg, border_radius=10)
        pygame.draw.rect(self.screen, (80, 80, 100), legend_bg, 2, border_radius=10)

        title = self.font.render("Легенда и управление", True, (255, 200, 100))
        self.screen.blit(title, (legend_x, legend_y))

        y_offset = legend_y + 45

        if y_offset + 30 < legend_bg.bottom - 10:
            colors_info = [
                ("Пустая клетка", (50, 50, 50)),
                ("Живое дерево", (34, 139, 34)),
                ("Горящее дерево", (255, 69, 0)),
            ]

            x_pos = legend_x + 10
            for i, (label, color) in enumerate(colors_info):
                if x_pos + 200 > legend_bg.right - 10:
                    break
                pygame.draw.rect(self.screen, color, (x_pos, y_offset, 20, 20), border_radius=4)
                pygame.draw.rect(self.screen, (255, 255, 255), (x_pos, y_offset, 20, 20), 2, border_radius=4)
                text = self.small_font.render(label, True, (220, 220, 220))
                self.screen.blit(text, (x_pos + 28, y_offset + 2))
                x_pos += 230

            y_offset += 40

        if y_offset + 28 < legend_bg.bottom - 10:
            control_title = self.medium_font.render("Клавиши управления:", True, (150, 200, 255))
            self.screen.blit(control_title, (legend_x + 10, y_offset))
            y_offset += 35

            controls = [
                ("[SPACE] — Пауза/Продолжить", "[R] — Перезапуск"),
                ("[+/-] — Изменить скорость", "[ESC] — Вернуться в меню"),
            ]

            for row in controls:
                if y_offset + 28 > legend_bg.bottom - 10:
                    break
                for i, control in enumerate(row):
                    if control and i * 400 + legend_x + 10 < legend_bg.right - 10:
                        x_pos = legend_x + 10 + i * 400
                        text = self.small_font.render(control, True, (200, 200, 200))
                        self.screen.blit(text, (x_pos, y_offset))
                y_offset += 26

        if y_offset + 35 < legend_bg.bottom - 10:
            y_offset += 10
            status_text = f"Скорость: {self.speed} FPS"
            if self.paused:
                status_text += "  |  ПАУЗА"

            status = self.medium_font.render(
                status_text, True, (255, 255, 100) if self.paused else (100, 255, 100)
            )
            self.screen.blit(status, (legend_x + 10, y_offset))

    def run(self):
        """Главный цикл визуализации"""
        clock = pygame.time.Clock()

        while self.running and self.simulation.generation < self.simulation.params.generations:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.simulation.__init__(self.simulation.params)
                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        self.speed = min(60, self.speed + 5)
                    elif event.key == pygame.K_MINUS:
                        self.speed = max(1, self.speed - 5)
                    elif event.key == pygame.K_ESCAPE:
                        return "menu"
                elif event.type == pygame.VIDEORESIZE:
                    self.width = event.w
                    self.height = event.h

            if not self.paused:
                self.simulation.update()

            for i in range(self.height):
                color_value = int(20 + (i / self.height) * 15)
                pygame.draw.line(
                    self.screen, (color_value, color_value, color_value + 10), (0, i), (self.width, i)
                )

            self.draw_grid()
            self.draw_info_panel()
            self.draw_legend()

            pygame.display.flip()
            clock.tick(self.speed)

        return "finished"


class ExperimentScreen:
    def __init__(self, width=1200, height=800):
        pygame.init()

        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Запуск экспериментов")

        self.font = pygame.font.Font(None, 40)
        self.medium_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 22)
        self.tiny_font = pygame.font.Font(None, 18)

        self.experiments = []
        self.current_experiment = 0
        self.running = False

    def run_experiments(self):
        """Запуск всех экспериментов"""
        experiments_params = [
            (
                "Детерминированный фон Нейман",
                SimulationParams(
                    rows=50,
                    cols=50,
                    initial_tree_percent=0.6,
                    initial_burning_percent=0.01,
                    generations=200,
                    neighborhood=NeighborhoodType.VON_NEUMANN,
                    deterministic=True,
                ),
            ),
            (
                "Детерминированный Мур",
                SimulationParams(
                    rows=50,
                    cols=50,
                    initial_tree_percent=0.6,
                    initial_burning_percent=0.01,
                    generations=200,
                    neighborhood=NeighborhoodType.MOORE,
                    deterministic=True,
                ),
            ),
            (
                "Стохастическая модель",
                SimulationParams(
                    rows=50,
                    cols=50,
                    initial_tree_percent=0.5,
                    initial_burning_percent=0.01,
                    generations=200,
                    neighborhood=NeighborhoodType.MOORE,
                    deterministic=False,
                    grow_probability=0.05,
                    spontaneous_fire_probability=0.0001,
                ),
            ),
            (
                "С возрастом деревьев",
                SimulationParams(
                    rows=50,
                    cols=50,
                    initial_tree_percent=0.6,
                    initial_burning_percent=0.01,
                    generations=200,
                    neighborhood=NeighborhoodType.MOORE,
                    deterministic=False,
                    grow_probability=0.1,
                    spontaneous_fire_probability=0.0005,
                    use_age=True,
                    max_age=50,
                ),
            ),
        ]

        self.experiments = []

        for idx, (label, params) in enumerate(experiments_params):
            self.current_experiment = idx
            sim = ForestFireSimulation(params)

            clock = pygame.time.Clock()

            while sim.generation < params.generations:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return None
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return "menu"
                    elif event.type == pygame.VIDEORESIZE:
                        self.width = event.w
                        self.height = event.h

                sim.update()

                for i in range(self.height):
                    color_value = int(20 + (i / self.height) * 15)
                    pygame.draw.line(
                        self.screen, (color_value, color_value, color_value + 10), (0, i), (self.width, i)
                    )

                title = self.font.render("Выполнение экспериментов", True, (255, 200, 100))
                self.screen.blit(title, (self.width // 2 - 250, 80))

                exp_text = self.medium_font.render(
                    f"Эксперимент {self.current_experiment + 1}/4: {label}", True, (200, 200, 255)
                )
                self.screen.blit(exp_text, (self.width // 2 - 280, 150))

                progress = sim.generation / params.generations
                bar_width = min(840, self.width - 360)
                bar_x = (self.width - bar_width) // 2
                progress_rect = pygame.Rect(bar_x, 220, bar_width, 45)
                pygame.draw.rect(self.screen, (40, 40, 50), progress_rect, border_radius=22)
                pygame.draw.rect(
                    self.screen, (50, 150, 255), (bar_x, 220, int(bar_width * progress), 45), border_radius=22
                )
                pygame.draw.rect(self.screen, (100, 100, 120), progress_rect, 3, border_radius=22)

                progress_text = self.medium_font.render(
                    f"{sim.generation}/{params.generations} поколений ({progress*100:.1f}%)",
                    True,
                    (255, 255, 255),
                )
                self.screen.blit(progress_text, (self.width // 2 - 150, 230))

                mini_y = 310
                mini_x = max(180, (self.width - 850) // 2)
                self.draw_mini_grid(sim, mini_x, mini_y)

                if sim.statistics:
                    stats = sim.statistics[-1]

                    stats_x = mini_x + 370
                    stats_bg = pygame.Rect(stats_x - 20, mini_y - 15, 360, 360)
                    pygame.draw.rect(self.screen, (30, 30, 40), stats_bg, border_radius=10)
                    pygame.draw.rect(self.screen, (80, 80, 100), stats_bg, 2, border_radius=10)

                    stats_y = mini_y

                    stats_title = self.medium_font.render("Текущая статистика", True, (255, 200, 100))
                    self.screen.blit(stats_title, (stats_x, stats_y))
                    stats_y += 40

                    total = params.rows * params.cols
                    stats_lines = [
                        (f"Живые: {stats.alive_trees} ({stats.alive_trees/total*100:.1f}%)", (100, 200, 100)),
                        (
                            f"Горящие: {stats.burning_trees} ({stats.burning_trees/total*100:.1f}%)",
                            (255, 120, 60),
                        ),
                        (
                            f"Пустые: {stats.empty_cells} ({stats.empty_cells/total*100:.1f}%)",
                            (150, 150, 150),
                        ),
                        ("", None),
                        (f"Плотность: {stats.forest_density:.4f}", (255, 255, 100)),
                        ("", None),
                        (f"Выросло: {stats.trees_grown}", (100, 255, 100)),
                        (f"Загорелось: {stats.trees_ignited}", (255, 100, 50)),
                        (f"Умерло: {stats.trees_died}", (150, 150, 150)),
                    ]

                    if params.use_age and stats.alive_trees > 0:
                        stats_lines.extend(
                            [
                                ("", None),
                                (f"Макс. возраст: {stats.max_age}", (200, 200, 200)),
                                (f"Ср. возраст: {stats.avg_age:.1f}", (200, 200, 200)),
                            ]
                        )

                    for line, color in stats_lines:
                        if stats_y + 26 > stats_bg.bottom - 10:
                            break
                        if line:
                            text = self.small_font.render(line, True, color if color else (200, 200, 200))
                            self.screen.blit(text, (stats_x + 10, stats_y))
                        stats_y += 26

                esc_text = self.small_font.render("[ESC] — Вернуться в меню", True, (180, 180, 200))
                esc_rect = esc_text.get_rect(center=(self.width // 2, self.height - 60))
                self.screen.blit(esc_text, esc_rect)

                pygame.display.flip()
                clock.tick(120)

            self.experiments.append((label, sim))

        return self.show_results()

    def draw_mini_grid(self, sim, x, y):
        """Отрисовка мини-версии сетки"""
        cell_size = 6
        grid_width = sim.params.cols * cell_size
        grid_height = sim.params.rows * cell_size

        grid_bg = pygame.Rect(x - 15, y - 15, grid_width + 30, grid_height + 30)
        pygame.draw.rect(self.screen, (30, 30, 40), grid_bg, border_radius=10)
        pygame.draw.rect(self.screen, (80, 80, 100), grid_bg, 2, border_radius=10)

        colors = {
            CellState.EMPTY: (50, 50, 50),
            CellState.TREE: (34, 139, 34),
            CellState.BURNING: (255, 69, 0),
        }

        for row in range(sim.params.rows):
            for col in range(sim.params.cols):
                state = sim.grid[row, col]
                color = colors[state]
                rect = pygame.Rect(x + col * cell_size, y + row * cell_size, cell_size, cell_size)
                pygame.draw.rect(self.screen, color, rect)

    def show_results(self):
        """Показать результаты и предложить построить графики"""
        plot_button = Button(
            self.width // 2 - 330, self.height - 180, 320, 60, "Показать графики", (70, 130, 180)
        )
        menu_button = Button(
            self.width // 2 + 10, self.height - 180, 320, 60, "Вернуться в меню", (180, 70, 70)
        )

        clock = pygame.time.Clock()

        while True:
            for i in range(self.height):
                color_value = int(20 + (i / self.height) * 15)
                pygame.draw.line(
                    self.screen, (color_value, color_value, color_value + 10), (0, i), (self.width, i)
                )

            title = self.font.render("Эксперименты завершены!", True, (100, 255, 100))
            self.screen.blit(title, (self.width // 2 - 230, 60))

            subtitle = self.medium_font.render("Результаты всех экспериментов", True, (180, 180, 200))
            self.screen.blit(subtitle, (self.width // 2 - 180, 110))

            results_bg = pygame.Rect(60, 160, self.width - 120, 420)
            pygame.draw.rect(self.screen, (30, 30, 40), results_bg, border_radius=10)
            pygame.draw.rect(self.screen, (80, 80, 100), results_bg, 2, border_radius=10)

            y_offset = 180
            headers = ["Эксперимент", "Плотность", "Живые", "Сгорело", "Выросло", "Пожары"]
            x_positions = [100, 450, 600, 730, 880, 1020]

            for i, header in enumerate(headers):
                color = (150, 200, 255)
                text = self.medium_font.render(header, True, color)
                self.screen.blit(text, (x_positions[i], y_offset))

            y_offset += 35
            pygame.draw.line(self.screen, (100, 100, 120), (80, y_offset), (self.width - 80, y_offset), 2)
            y_offset += 20

            for idx, (label, sim) in enumerate(self.experiments):
                final = sim.statistics[-1]

                if idx % 2 == 0:
                    row_bg = pygame.Rect(70, y_offset - 5, self.width - 140, 75)
                    pygame.draw.rect(self.screen, (25, 25, 35), row_bg, border_radius=5)

                name_text = self.small_font.render(f"{idx + 1}. {label}", True, (200, 255, 200))
                self.screen.blit(name_text, (100, y_offset))

                params_info = []
                if sim.params.neighborhood == NeighborhoodType.VON_NEUMANN:
                    params_info.append("фон Нейман")
                else:
                    params_info.append("Мур")

                if sim.params.deterministic:
                    params_info.append("детерм.")
                else:
                    params_info.append("стохаст.")

                if sim.params.use_age:
                    params_info.append(f"возраст <={sim.params.max_age}")

                params_text = self.tiny_font.render(f"({', '.join(params_info)})", True, (150, 150, 170))
                self.screen.blit(params_text, (100, y_offset + 22))

                data = [
                    f"{final.forest_density:.4f}",
                    f"{final.alive_trees}",
                    f"{sim.total_trees_died}",
                    f"{sim.total_trees_grown}",
                    f"{sim.total_fires}",
                ]

                colors = [
                    (255, 255, 100),
                    (100, 200, 100),
                    (255, 100, 80),
                    (100, 255, 100),
                    (255, 150, 50),
                ]

                for i, (value, color) in enumerate(zip(data, colors)):
                    text = self.small_font.render(value, True, color)
                    self.screen.blit(text, (x_positions[i + 1], y_offset + 5))

                y_offset += 85

            plot_button.draw(self.screen, self.medium_font)
            menu_button.draw(self.screen, self.medium_font)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return None
                elif event.type == pygame.VIDEORESIZE:
                    self.width = event.w
                    self.height = event.h

                if plot_button.handle_event(event):
                    self.plot_statistics()

                if menu_button.handle_event(event):
                    return "menu"

            pygame.display.flip()
            clock.tick(60)

    def plot_statistics(self):
        """Построение графиков статистики"""
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Анализ симуляции "Лесной пожар"', fontsize=20, fontweight="bold")
        fig.patch.set_facecolor("#f0f0f0")

        colors_palette = ["#2E7D32", "#1565C0", "#D84315", "#7B1FA2"]

        for idx, (label, sim) in enumerate(self.experiments):
            color = colors_palette[idx]

            generations = [s.generation for s in sim.statistics]
            alive_trees = [s.alive_trees for s in sim.statistics]
            burning_trees = [s.burning_trees for s in sim.statistics]
            forest_density = [s.forest_density for s in sim.statistics]
            trees_grown = [s.trees_grown for s in sim.statistics]
            trees_ignited = [s.trees_ignited for s in sim.statistics]

            axes[0, 0].plot(generations, alive_trees, label=f"{label}", color=color, linewidth=2, alpha=0.8)

            axes[0, 1].plot(generations, forest_density, label=label, color=color, linewidth=2, alpha=0.8)

            axes[0, 2].plot(generations, trees_grown, label=label, color=color, linewidth=2, alpha=0.7)

            axes[1, 0].plot(generations, trees_ignited, label=label, color=color, linewidth=2, alpha=0.7)

            if sim.params.use_age:
                avg_ages = [s.avg_age for s in sim.statistics]
                axes[1, 1].plot(generations, avg_ages, label=label, color=color, linewidth=2, alpha=0.8)

            total_grown = np.cumsum(trees_grown)
            total_died = [s.trees_died for s in sim.statistics]
            total_died_cum = np.cumsum(total_died)

            axes[1, 2].plot(
                generations, total_grown, label=f"{label} (выросло)", color=color, linewidth=2, alpha=0.8
            )
            axes[1, 2].plot(
                generations,
                total_died_cum,
                label=f"{label} (сгорело)",
                color=color,
                linewidth=2,
                linestyle="--",
                alpha=0.6,
            )

        titles = [
            "Популяция живых деревьев",
            "Плотность леса",
            "Деревья, выросшие за поколение",
            "Деревья, загоревшиеся за поколение",
            "Средний возраст деревьев",
            "Совокупная статистика",
        ]

        for ax, title in zip(axes.flat, titles):
            ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
            ax.set_xlabel("Поколение", fontsize=11, fontweight="bold")
            ax.set_ylabel("Количество", fontsize=11, fontweight="bold")
            ax.legend(fontsize=9, loc="best", framealpha=0.9)
            ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.7)
            ax.set_facecolor("#fafafa")

            ax.tick_params(labelsize=10)
            for spine in ax.spines.values():
                spine.set_edgecolor("#cccccc")
                spine.set_linewidth(1.5)

        plt.tight_layout()
        plt.savefig("forest_fire_analysis.png", dpi=200, bbox_inches="tight", facecolor="#f0f0f0")
        plt.show()


class ResultScreen:
    def __init__(self, simulation: ForestFireSimulation):
        pygame.init()

        self.width = 1100
        self.height = 750

        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Результаты симуляции")
        self.simulation = simulation

        self.font = pygame.font.Font(None, 44)
        self.medium_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 22)
        self.tiny_font = pygame.font.Font(None, 18)

    def run(self):
        plot_button = Button(
            self.width // 2 - 330, self.height - 130, 320, 60, "Показать графики", (70, 130, 180)
        )
        menu_button = Button(
            self.width // 2 + 10, self.height - 130, 320, 60, "Вернуться в меню", (50, 150, 50)
        )

        clock = pygame.time.Clock()

        while True:
            for i in range(self.height):
                color_value = int(20 + (i / self.height) * 15)
                pygame.draw.line(
                    self.screen, (color_value, color_value, color_value + 10), (0, i), (self.width, i)
                )

            title = self.font.render("Симуляция завершена!", True, (100, 255, 100))
            title_rect = title.get_rect(center=(self.width // 2, 60))
            self.screen.blit(title, title_rect)

            table_bg = pygame.Rect(60, 120, self.width - 120, 470)
            pygame.draw.rect(self.screen, (30, 30, 40), table_bg, border_radius=10)
            pygame.draw.rect(self.screen, (80, 80, 100), table_bg, 2, border_radius=10)

            if self.simulation.statistics:
                final = self.simulation.statistics[-1]
                total = self.simulation.params.rows * self.simulation.params.cols

                y_offset = 145

                section_title = self.medium_font.render("Финальная статистика", True, (255, 200, 100))
                section_rect = section_title.get_rect(center=(self.width // 2, y_offset))
                self.screen.blit(section_title, section_rect)
                y_offset += 50

                headers = ["Параметр", "Значение"]
                x_positions = [120, 650]

                for i, header in enumerate(headers):
                    text = self.medium_font.render(header, True, (150, 200, 255))
                    self.screen.blit(text, (x_positions[i], y_offset))

                y_offset += 35
                pygame.draw.line(self.screen, (100, 100, 120), (80, y_offset), (self.width - 80, y_offset), 2)
                y_offset += 15

                table_data = [
                    ("Всего поколений", f"{final.generation}", (200, 200, 255)),
                    ("", "", None),
                    (
                        "Живых деревьев",
                        f"{final.alive_trees} ({final.alive_trees/total*100:.1f}%)",
                        (100, 200, 100),
                    ),
                    (
                        "Горящих деревьев",
                        f"{final.burning_trees} ({final.burning_trees/total*100:.1f}%)",
                        (255, 120, 60),
                    ),
                    (
                        "Пустых клеток",
                        f"{final.empty_cells} ({final.empty_cells/total*100:.1f}%)",
                        (150, 150, 150),
                    ),
                    ("", "", None),
                    ("Плотность леса", f"{final.forest_density:.4f}", (255, 255, 100)),
                    ("", "", None),
                    ("Всего выросло", f"{self.simulation.total_trees_grown}", (100, 255, 100)),
                    ("Всего сгорело", f"{self.simulation.total_trees_died}", (255, 100, 80)),
                    ("Количество пожаров", f"{self.simulation.total_fires}", (255, 150, 50)),
                ]

                if self.simulation.params.use_age:
                    table_data.extend(
                        [
                            ("", "", None),
                            ("Макс. возраст (рекорд)", f"{self.simulation.max_age_ever}", (200, 200, 200)),
                            ("Средний возраст", f"{final.avg_age:.1f}", (200, 200, 200)),
                        ]
                    )

                row_idx = 0
                for param, value, color in table_data:
                    if param:
                        if row_idx % 2 == 0:
                            row_bg = pygame.Rect(80, y_offset - 3, self.width - 160, 32)
                            pygame.draw.rect(self.screen, (25, 25, 35), row_bg, border_radius=4)

                        param_text = self.small_font.render(param, True, (220, 220, 220))
                        self.screen.blit(param_text, (120, y_offset))

                        value_text = self.small_font.render(value, True, color)
                        self.screen.blit(value_text, (650, y_offset))

                        row_idx += 1

                    y_offset += 30 if param else 10

            plot_button.draw(self.screen, self.medium_font)
            menu_button.draw(self.screen, self.medium_font)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.VIDEORESIZE:
                    self.width = event.w
                    self.height = event.h

                if plot_button.handle_event(event):
                    self.show_plots()

                if menu_button.handle_event(event):
                    return

            pygame.display.flip()
            clock.tick(60)

    def show_plots(self):
        """Показать графики для одной симуляции"""
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Анализ симуляции "Лесной пожар"', fontsize=20, fontweight="bold")
        fig.patch.set_facecolor("#f0f0f0")

        sim = self.simulation

        generations = [s.generation for s in sim.statistics]
        alive_trees = [s.alive_trees for s in sim.statistics]
        burning_trees = [s.burning_trees for s in sim.statistics]
        forest_density = [s.forest_density for s in sim.statistics]
        trees_grown = [s.trees_grown for s in sim.statistics]
        trees_ignited = [s.trees_ignited for s in sim.statistics]
        trees_died = [s.trees_died for s in sim.statistics]

        axes[0, 0].plot(generations, alive_trees, label="Живые", color="#2E7D32", linewidth=2.5, alpha=0.9)
        axes[0, 0].plot(
            generations,
            burning_trees,
            label="Горящие",
            color="#D84315",
            linestyle="--",
            linewidth=2,
            alpha=0.8,
        )
        axes[0, 0].set_title("Популяция деревьев", fontsize=14, fontweight="bold", pad=15)
        axes[0, 0].set_xlabel("Поколение", fontsize=11, fontweight="bold")
        axes[0, 0].set_ylabel("Количество", fontsize=11, fontweight="bold")
        axes[0, 0].legend(fontsize=11, loc="best", framealpha=0.9)
        axes[0, 0].grid(True, alpha=0.3, linestyle="--", linewidth=0.7)
        axes[0, 0].set_facecolor("#fafafa")

        axes[0, 1].plot(generations, forest_density, color="#1565C0", linewidth=2.5, alpha=0.9)
        axes[0, 1].fill_between(generations, forest_density, alpha=0.3, color="#1565C0")
        axes[0, 1].set_title("Плотность леса", fontsize=14, fontweight="bold", pad=15)
        axes[0, 1].set_xlabel("Поколение", fontsize=11, fontweight="bold")
        axes[0, 1].set_ylabel("Плотность", fontsize=11, fontweight="bold")
        axes[0, 1].grid(True, alpha=0.3, linestyle="--", linewidth=0.7)
        axes[0, 1].set_facecolor("#fafafa")

        axes[0, 2].plot(generations, trees_grown, color="#388E3C", linewidth=2, alpha=0.8)
        axes[0, 2].fill_between(generations, trees_grown, alpha=0.3, color="#388E3C")
        axes[0, 2].set_title("Деревья, выросшие за поколение", fontsize=14, fontweight="bold", pad=15)
        axes[0, 2].set_xlabel("Поколение", fontsize=11, fontweight="bold")
        axes[0, 2].set_ylabel("Количество", fontsize=11, fontweight="bold")
        axes[0, 2].grid(True, alpha=0.3, linestyle="--", linewidth=0.7)
        axes[0, 2].set_facecolor("#fafafa")

        axes[1, 0].plot(generations, trees_ignited, color="#FF6F00", linewidth=2, alpha=0.8)
        axes[1, 0].fill_between(generations, trees_ignited, alpha=0.3, color="#FF6F00")
        axes[1, 0].set_title("Деревья, загоревшиеся за поколение", fontsize=14, fontweight="bold", pad=15)
        axes[1, 0].set_xlabel("Поколение", fontsize=11, fontweight="bold")
        axes[1, 0].set_ylabel("Количество", fontsize=11, fontweight="bold")
        axes[1, 0].grid(True, alpha=0.3, linestyle="--", linewidth=0.7)
        axes[1, 0].set_facecolor("#fafafa")

        if sim.params.use_age:
            avg_ages = [s.avg_age for s in sim.statistics]
            axes[1, 1].plot(generations, avg_ages, color="#6A1B9A", linewidth=2.5, alpha=0.9)
            axes[1, 1].fill_between(generations, avg_ages, alpha=0.3, color="#6A1B9A")
            axes[1, 1].set_title("Средний возраст деревьев", fontsize=14, fontweight="bold", pad=15)
            axes[1, 1].set_xlabel("Поколение", fontsize=11, fontweight="bold")
            axes[1, 1].set_ylabel("Возраст", fontsize=11, fontweight="bold")
            axes[1, 1].grid(True, alpha=0.3, linestyle="--", linewidth=0.7)
            axes[1, 1].set_facecolor("#fafafa")
        else:
            axes[1, 1].text(
                0.5,
                0.5,
                "Возраст не учитывается\nв данной симуляции",
                ha="center",
                va="center",
                transform=axes[1, 1].transAxes,
                fontsize=14,
                color="#666666",
            )
            axes[1, 1].set_title("Средний возраст деревьев", fontsize=14, fontweight="bold", pad=15)
            axes[1, 1].set_facecolor("#fafafa")

        total_grown = np.cumsum(trees_grown)
        total_died = np.cumsum(trees_died)

        axes[1, 2].plot(generations, total_grown, label="Выросло", color="#2E7D32", linewidth=2.5, alpha=0.9)
        axes[1, 2].plot(
            generations,
            total_died,
            label="Сгорело",
            color="#D84315",
            linestyle="--",
            linewidth=2.5,
            alpha=0.9,
        )
        axes[1, 2].fill_between(generations, total_grown, alpha=0.2, color="#2E7D32")
        axes[1, 2].fill_between(generations, total_died, alpha=0.2, color="#D84315")
        axes[1, 2].set_title("Совокупная статистика", fontsize=14, fontweight="bold", pad=15)
        axes[1, 2].set_xlabel("Поколение", fontsize=11, fontweight="bold")
        axes[1, 2].set_ylabel("Количество", fontsize=11, fontweight="bold")
        axes[1, 2].legend(fontsize=11, loc="best", framealpha=0.9)
        axes[1, 2].grid(True, alpha=0.3, linestyle="--", linewidth=0.7)
        axes[1, 2].set_facecolor("#fafafa")

        for ax in axes.flat:
            ax.tick_params(labelsize=10)
            for spine in ax.spines.values():
                spine.set_edgecolor("#cccccc")
                spine.set_linewidth(1.5)

        plt.tight_layout()
        plt.savefig("forest_fire_analysis.png", dpi=200, bbox_inches="tight", facecolor="#f0f0f0")
        plt.show()


def main():
    """Главная функция программы"""
    current_screen = "menu"

    while current_screen:
        if current_screen == "menu":
            menu = MenuScreen()
            result = menu.run()
            pygame.quit()

            if result == "simulation":
                current_screen = "parameters"
            elif result == "experiments":
                current_screen = "experiments"
            else:
                break

        elif current_screen == "parameters":
            param_screen = ParameterScreen()
            result = param_screen.run()
            pygame.quit()

            if result == "back":
                current_screen = "menu"
            elif result is None:
                break
            elif isinstance(result, SimulationParams):
                sim = ForestFireSimulation(result)
                viz = Visualization(sim)
                viz_result = viz.run()
                pygame.quit()

                if viz_result == "menu":
                    current_screen = "menu"
                elif viz_result == "finished":
                    result_screen = ResultScreen(sim)
                    result_screen.run()
                    pygame.quit()
                    current_screen = "menu"
                else:
                    break

        elif current_screen == "experiments":
            exp_screen = ExperimentScreen()
            result = exp_screen.run_experiments()
            pygame.quit()

            if result == "menu":
                current_screen = "menu"
            else:
                break


if __name__ == "__main__":
    main()
