import pygame
import random
import time
import math

pygame.init()


SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Сеть Петри - Система управления производством")


try:
    font = pygame.font.SysFont("Arial", 18)
    large_font = pygame.font.SysFont("Arial", 28)
    small_font = pygame.font.SysFont("Arial", 14)
    title_font = pygame.font.SysFont("Arial", 20)
    tiny_font = pygame.font.SysFont("Arial", 12)
except:
    font = pygame.font.Font(None, 20)
    large_font = pygame.font.Font(None, 32)
    small_font = pygame.font.Font(None, 16)
    title_font = pygame.font.Font(None, 24)
    tiny_font = pygame.font.Font(None, 14)


BG_COLOR = (245, 245, 245)
PLACE_COLOR = (220, 220, 220)
PLACE_BORDER = (80, 80, 80)
TRANSITION_COLOR = (255, 255, 255)
TRANSITION_BORDER = (100, 100, 100)
ARC_COLOR = (120, 120, 120)
TOKEN_COLOR = (40, 40, 40)
TEXT_COLOR = (30, 30, 30)
LEGEND_BG = (250, 250, 250)
ACTIVE_COLOR = (200, 60, 60)


camera_x = 0
camera_y = 0
zoom = 0.7
min_zoom = 0.3
max_zoom = 2.5


dragging = False
last_mouse_pos = (0, 0)
show_stats_panel = True
show_legend_panel = True


class Token:
    def __init__(self, size=None, phase=None):
        self.size = size
        self.phase = phase
        self.processing_start_time = None


class Place:
    def __init__(self, name, pos, display_name):
        self.name = name
        self.base_pos = pos
        self.display_name = display_name
        self.tokens = []

    @property
    def pos(self):
        return (
            int((self.base_pos[0] + camera_x) * zoom + SCREEN_WIDTH / 2),
            int((self.base_pos[1] + camera_y) * zoom + SCREEN_HEIGHT / 2),
        )


class Transition:
    def __init__(self, name, pos, display_name, width=170, height=70):
        self.name = name
        self.base_pos = pos
        self.display_name = display_name
        self.active = False
        self.activation_time = 0
        self.base_width = width
        self.base_height = height

    @property
    def pos(self):
        return (
            int((self.base_pos[0] + camera_x) * zoom + SCREEN_WIDTH / 2),
            int((self.base_pos[1] + camera_y) * zoom + SCREEN_HEIGHT / 2),
        )

    @property
    def width(self):
        return int(self.base_width * zoom)

    @property
    def height(self):
        return int(self.base_height * zoom)


class MovingToken:
    def __init__(self, start_pos, end_pos, duration=0.6):
        self.start_base_pos = start_pos
        self.end_base_pos = end_pos
        self.t_start = time.time()
        self.duration = duration

    def get_current_pos(self):
        progress = (time.time() - self.t_start) / self.duration
        if progress < 0.5:
            smooth = 2 * progress * progress
        else:
            smooth = 1 - pow(-2 * progress + 2, 2) / 2

        base_x = self.start_base_pos[0] + (self.end_base_pos[0] - self.start_base_pos[0]) * smooth
        base_y = self.start_base_pos[1] + (self.end_base_pos[1] - self.start_base_pos[1]) * smooth

        return (
            int((base_x + camera_x) * zoom + SCREEN_WIDTH / 2),
            int((base_y + camera_y) * zoom + SCREEN_HEIGHT / 2),
        )


moving_tokens = []
event_log = []


BASE_CENTER_X = -800
BASE_CENTER_Y = 0

COLUMN_SPACING = 400
ROW_SPACING = 350

places = {
    "P1": Place("P1", (BASE_CENTER_X + COLUMN_SPACING, BASE_CENTER_Y - ROW_SPACING), "P1\nДанные\nдатчика 1"),
    "P2": Place("P2", (BASE_CENTER_X + COLUMN_SPACING, BASE_CENTER_Y), "P2\nДанные\nдатчика 2"),
    "P3": Place("P3", (BASE_CENTER_X + COLUMN_SPACING, BASE_CENTER_Y + ROW_SPACING), "P3\nДанные\nдатчика 3"),
    "P4": Place("P4", (BASE_CENTER_X + COLUMN_SPACING * 5, BASE_CENTER_Y), "P4\nЭВМ\nсвободна"),
    "P5": Place(
        "P5", (BASE_CENTER_X + COLUMN_SPACING * 3, BASE_CENTER_Y - ROW_SPACING * 2.0), "P5\nОчередь\nзаданий"
    ),
    "P6": Place(
        "P6", (BASE_CENTER_X + COLUMN_SPACING * 3, BASE_CENTER_Y - ROW_SPACING), "P6\nОбработка\nдатчика 1"
    ),
    "P7": Place("P7", (BASE_CENTER_X + COLUMN_SPACING * 3, BASE_CENTER_Y), "P7\nОбработка\nдатчика 2"),
    "P8": Place(
        "P8", (BASE_CENTER_X + COLUMN_SPACING * 3, BASE_CENTER_Y + ROW_SPACING), "P8\nОбработка\nдатчика 3"
    ),
    "P9": Place("P9", (BASE_CENTER_X + COLUMN_SPACING * 5, BASE_CENTER_Y + ROW_SPACING), "P9\nТаймер\nцикла"),
}

transitions = {
    "T1": Transition(
        "T1", (BASE_CENTER_X + COLUMN_SPACING * 0.5, BASE_CENTER_Y - ROW_SPACING), "T1\nГенерация\nданных 1"
    ),
    "T2": Transition("T2", (BASE_CENTER_X + COLUMN_SPACING * 0.5, BASE_CENTER_Y), "T2\nГенерация\nданных 2"),
    "T3": Transition(
        "T3", (BASE_CENTER_X + COLUMN_SPACING * 0.5, BASE_CENTER_Y + ROW_SPACING), "T3\nГенерация\nданных 3"
    ),
    "T4": Transition(
        "T4", (BASE_CENTER_X + COLUMN_SPACING * 2, BASE_CENTER_Y - ROW_SPACING), "T4\nНачало\nобработки 1"
    ),
    "T5": Transition("T5", (BASE_CENTER_X + COLUMN_SPACING * 2, BASE_CENTER_Y), "T5\nНачало\nобработки 2"),
    "T6": Transition(
        "T6", (BASE_CENTER_X + COLUMN_SPACING * 2, BASE_CENTER_Y + ROW_SPACING), "T6\nНачало\nобработки 3"
    ),
    "T7": Transition(
        "T7", (BASE_CENTER_X + COLUMN_SPACING * 4, BASE_CENTER_Y - ROW_SPACING), "T7\nЗавершение\nобработки 1"
    ),
    "T8": Transition(
        "T8", (BASE_CENTER_X + COLUMN_SPACING * 4, BASE_CENTER_Y), "T8\nЗавершение\nобработки 2"
    ),
    "T9": Transition(
        "T9", (BASE_CENTER_X + COLUMN_SPACING * 4, BASE_CENTER_Y + ROW_SPACING), "T9\nЗавершение\nобработки 3"
    ),
    "T10": Transition(
        "T10",
        (BASE_CENTER_X + COLUMN_SPACING * 2.5, BASE_CENTER_Y - ROW_SPACING * 2.0),
        "T10\nОбработка\nочереди",
    ),
    "T11": Transition(
        "T11", (BASE_CENTER_X + COLUMN_SPACING * 5.5, BASE_CENTER_Y + ROW_SPACING), "T11\nСмена\nцикла"
    ),
}


places["P4"].tokens = [Token()]
places["P9"].tokens = [Token(phase=0)]

sim_time = 0.0
speed = 50
paused = False
simulation_finished = False

events = [
    (random.uniform(9, 15), "generate", 1),
    (random.uniform(9, 15), "generate", 2),
    (random.uniform(9, 15), "generate", 3),
]
events.sort(key=lambda x: x[0])

current_processing = {"place": None, "start_time": None, "initial_size": None, "sensor_num": None}

stats = {
    "processed": 0,
    "queued": 0,
    "free_cycles": 0,
    "max_queue_size": 0,
    "total_cycles": 0,
    "generated": {1: 0, 2: 0, 3: 0},
}


def add_to_log(message):
    global event_log
    hours = int(sim_time // 3600)
    minutes = int((sim_time % 3600) // 60)
    seconds = int(sim_time % 60)
    timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    event_log.append((timestamp, message))
    if len(event_log) > 20:
        event_log.pop(0)


def get_connection_point(obj, target_pos, is_place=True):
    obj_center_screen = obj.pos

    dx_obj_to_target = target_pos[0] - obj_center_screen[0]
    dy_obj_to_target = target_pos[1] - obj_center_screen[1]

    length = math.sqrt(dx_obj_to_target**2 + dy_obj_to_target**2)

    if length == 0:
        return obj_center_screen

    unit_dx = dx_obj_to_target / length
    unit_dy = dy_obj_to_target / length

    if is_place:
        radius = int(75 * zoom)
        return (obj_center_screen[0] + unit_dx * radius, obj_center_screen[1] + unit_dy * radius)
    else:
        half_w = obj.width / 2
        half_h = obj.height / 2

        if unit_dx == 0:
            return (obj_center_screen[0], obj_center_screen[1] + unit_dy * half_h)
        if unit_dy == 0:
            return (obj_center_screen[0] + unit_dx * half_w, obj_center_screen[1])

        angle = math.atan2(unit_dy, unit_dx)

        cos_sq = math.cos(angle) ** 2
        sin_sq = math.sin(angle) ** 2

        term1 = cos_sq / (half_w**2) if half_w != 0 else float("inf")
        term2 = sin_sq / (half_h**2) if half_h != 0 else float("inf")

        if term1 == float("inf") and term2 == float("inf"):
            return obj_center_screen

        r_sq = 1 / (term1 + term2)
        r = math.sqrt(r_sq)

        return (obj_center_screen[0] + r * math.cos(angle), obj_center_screen[1] + r * math.sin(angle))


def draw_curved_arrow(
    surface,
    color,
    src_obj,
    dst_obj,
    width=2,
    curve_offset=0,
    src_is_place=True,
    dst_is_place=True,
    arrow_scale=1.0,
):
    start = get_connection_point(src_obj, dst_obj.pos, src_is_place)
    end = get_connection_point(dst_obj, src_obj.pos, dst_is_place)

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx**2 + dy**2)

    if length == 0:
        return

    arrow_color = ARC_COLOR

    if curve_offset != 0:
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2

        perp_x = -dy / length
        perp_y = dx / length

        control_x = mid_x + perp_x * curve_offset * zoom * arrow_scale
        control_y = mid_y + perp_y * curve_offset * zoom * arrow_scale

        points = []
        steps = 30
        for i in range(steps + 1):
            t = i / steps
            x = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control_x + t**2 * end[0]
            y = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control_y + t**2 * end[1]
            points.append((x, y))

        if len(points) > 1:
            line_width = max(2, int(width * zoom * 1.2))
            pygame.draw.lines(surface, (150, 150, 150), False, points, line_width + 1)
            pygame.draw.lines(surface, arrow_color, False, points, line_width)

        if len(points) >= 2:
            last_point = points[-1]
            prev_point = points[-2]
            arrow_dx = last_point[0] - prev_point[0]
            arrow_dy = last_point[1] - prev_point[1]
            angle = math.atan2(arrow_dy, arrow_dx)

            arrow_size = int(16 * zoom)
            p1 = last_point
            p2 = (
                last_point[0] - arrow_size * math.cos(angle - math.pi / 6),
                last_point[1] - arrow_size * math.sin(angle - math.pi / 6),
            )
            p3 = (
                last_point[0] - arrow_size * math.cos(angle + math.pi / 6),
                last_point[1] - arrow_size * math.sin(angle + math.pi / 6),
            )

            shadow_offset = 2
            pygame.draw.polygon(
                surface,
                (80, 80, 80),
                [
                    (p1[0] + shadow_offset, p1[1] + shadow_offset),
                    (p2[0] + shadow_offset, p2[1] + shadow_offset),
                    (p3[0] + shadow_offset, p3[1] + shadow_offset),
                ],
            )
            pygame.draw.polygon(surface, arrow_color, [p1, p2, p3])
    else:
        line_width = max(2, int(width * zoom * 1.2))
        pygame.draw.line(
            surface, (150, 150, 150), (start[0] + 2, start[1] + 2), (end[0] + 2, end[1] + 2), line_width + 1
        )
        pygame.draw.line(surface, arrow_color, start, end, line_width)

        arrow_size = int(16 * zoom)
        angle = math.atan2(dy, dx)

        p1 = end
        p2 = (
            end[0] - arrow_size * math.cos(angle - math.pi / 6),
            end[1] - arrow_size * math.sin(angle - math.pi / 6),
        )
        p3 = (
            end[0] - arrow_size * math.cos(angle + math.pi / 6),
            end[1] - arrow_size * math.sin(angle + math.pi / 6),
        )

        shadow_offset = 2
        pygame.draw.polygon(
            surface,
            (80, 80, 80),
            [
                (p1[0] + shadow_offset, p1[1] + shadow_offset),
                (p2[0] + shadow_offset, p2[1] + shadow_offset),
                (p3[0] + shadow_offset, p3[1] + shadow_offset),
            ],
        )
        pygame.draw.polygon(surface, arrow_color, [p1, p2, p3])


running = True
last_real_time = time.time()
final_report_shown = False


while running:
    current_real_time = time.time()
    dt_real = current_real_time - last_real_time
    last_real_time = current_real_time

    if sim_time >= 18000 and not simulation_finished:
        simulation_finished = True
        paused = True
        add_to_log("✓ Симуляция завершена (5 часов)")

    if not paused and not simulation_finished:
        dt_sim = dt_real * speed
        sim_time += dt_sim

        if current_processing["place"]:
            processing_place = current_processing["place"]
            if places[processing_place].tokens:
                token = places[processing_place].tokens[0]
                processing_time = sim_time - current_processing["start_time"]
                processed_amount = processing_time * 1000

                token.size = max(0, current_processing["initial_size"] - processed_amount)

        while events and events[0][0] <= sim_time:
            event_time, action, arg = events.pop(0)

            if action == "generate":
                sensor = arg
                size = random.uniform(2000, 4000)
                token = Token(size=size)
                places[f"P{sensor}"].tokens.append(token)
                moving_tokens.append(
                    MovingToken(transitions[f"T{sensor}"].base_pos, places[f"P{sensor}"].base_pos)
                )

                next_time = event_time + random.uniform(9, 15)
                events.append((next_time, "generate", sensor))
                events.sort(key=lambda x: x[0])
                transitions[f"T{sensor}"].active = True
                transitions[f"T{sensor}"].activation_time = time.time()
                stats["generated"][sensor] += 1
                add_to_log(f"T{sensor}: Сгенерированы данные датчика {sensor} ({int(size)} симв)")

            elif action == "finish_processing":
                processing_place, sensor_num = arg

                if places[processing_place].tokens:
                    token = places[processing_place].tokens.pop(0)

                    if token.size > 0:
                        places["P5"].tokens.append(token)
                        stats["queued"] += 1
                        moving_tokens.append(
                            MovingToken(places[processing_place].base_pos, places["P5"].base_pos)
                        )
                        add_to_log(f"T{sensor_num+7}: Остаток {int(token.size)} симв → очередь")
                    else:
                        stats["processed"] += 1
                        add_to_log(f"T{sensor_num+7}: Датчик {sensor_num+1} обработан полностью")

                places["P4"].tokens.append(Token())
                moving_tokens.append(
                    MovingToken(transitions[f"T{sensor_num+7}"].base_pos, places["P4"].base_pos)
                )

                current_phase = current_processing["sensor_num"]
                next_phase = (current_phase + 1) % 3
                places["P9"].tokens.append(Token(phase=next_phase))
                moving_tokens.append(
                    MovingToken(transitions[f"T{sensor_num+7}"].base_pos, places["P9"].base_pos)
                )

                t_num = 7 + sensor_num
                if t_num <= 9:
                    transitions[f"T{t_num}"].active = True
                    transitions[f"T{t_num}"].activation_time = time.time()

                current_processing["place"] = None
                current_processing["start_time"] = None
                current_processing["initial_size"] = None
                current_processing["sensor_num"] = None

            elif action == "change_cycle":
                previous_phase = arg
                stats["free_cycles"] += 1

                next_phase = (previous_phase + 1) % 3
                places["P9"].tokens.append(Token(phase=next_phase))

                moving_tokens.append(MovingToken(transitions["T11"].base_pos, places["P9"].base_pos))
                moving_tokens.append(MovingToken(transitions["T11"].base_pos, places["P4"].base_pos))
                places["P4"].tokens.append(Token())
                transitions["T11"].active = True
                transitions["T11"].activation_time = time.time()
                add_to_log(f"T11: Свободный цикл, фаза {previous_phase} → {next_phase}")

        if len(places["P4"].tokens) > 0 and len(places["P9"].tokens) > 0 and not current_processing["place"]:

            phase_token = places["P9"].tokens[0]
            current_phase = phase_token.phase

            sensor_place_name = f"P{current_phase + 1}"
            processing_place_name = f"P{current_phase + 6}"

            token_to_process = None
            source_pos = None
            trans_name = None

            stats["total_cycles"] += 1

            if places[sensor_place_name].tokens:
                places["P4"].tokens.pop()
                places["P9"].tokens.pop(0)

                token_to_process = places[sensor_place_name].tokens.pop(0)
                places[processing_place_name].tokens.append(token_to_process)
                source_pos = places[sensor_place_name].base_pos
                trans_name = f"T{current_phase + 4}"

                add_to_log(f"{trans_name}: Начало обработки датчика {current_phase + 1}")

            elif places["P5"].tokens:
                places["P4"].tokens.pop()
                places["P9"].tokens.pop(0)

                token_to_process = places["P5"].tokens.pop(0)
                places[processing_place_name].tokens.append(token_to_process)
                source_pos = places["P5"].base_pos
                trans_name = "T10"

                add_to_log(f"T10: Обработка из очереди (для фазы {current_phase + 1})")

            else:
                places["P4"].tokens.pop()
                places["P9"].tokens.pop(0)

                trans_name = "T11"

                events.append((sim_time + 3, "change_cycle", current_phase))
                events.sort(key=lambda x: x[0])
                add_to_log(f"T11: Начало свободного цикла (фаза {current_phase + 1})")

            if trans_name:
                transitions[trans_name].active = True
                transitions[trans_name].activation_time = time.time()

                moving_tokens.append(MovingToken(places["P4"].base_pos, transitions[trans_name].base_pos))
                moving_tokens.append(MovingToken(places["P9"].base_pos, transitions[trans_name].base_pos))

                if token_to_process:
                    current_processing["place"] = processing_place_name
                    current_processing["start_time"] = sim_time
                    current_processing["initial_size"] = token_to_process.size
                    current_processing["sensor_num"] = current_phase

                    events.append((sim_time + 3, "finish_processing", (processing_place_name, current_phase)))
                    events.sort(key=lambda x: x[0])

                    if source_pos:
                        moving_tokens.append(MovingToken(source_pos, places[processing_place_name].base_pos))

        current_queue_size = len(places["P5"].tokens)
        stats["max_queue_size"] = max(stats["max_queue_size"], current_queue_size)

    screen.fill(BG_COLOR)

    if simulation_finished and not final_report_shown:
        final_report_shown = True

    if simulation_finished:

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(230)
        overlay.fill((240, 240, 240))
        screen.blit(overlay, (0, 0))

        report_width = 800
        report_height = 700
        report_x = (SCREEN_WIDTH - report_width) // 2
        report_y = (SCREEN_HEIGHT - report_height) // 2

        shadow_rect = pygame.Rect(report_x + 6, report_y + 6, report_width, report_height)
        pygame.draw.rect(screen, (150, 150, 150), shadow_rect, border_radius=15)

        report_rect = pygame.Rect(report_x, report_y, report_width, report_height)
        pygame.draw.rect(screen, (255, 255, 255), report_rect, border_radius=15)
        pygame.draw.rect(screen, (100, 100, 100), report_rect, 3, border_radius=15)

        title_text = large_font.render("ИТОГОВЫЙ ОТЧЕТ СИМУЛЯЦИИ", True, (40, 40, 40))
        screen.blit(title_text, (report_x + (report_width - title_text.get_width()) // 2, report_y + 20))

        pygame.draw.line(
            screen,
            (200, 200, 200),
            (report_x + 40, report_y + 60),
            (report_x + report_width - 40, report_y + 60),
            2,
        )

        hours = int(sim_time // 3600)
        minutes = int((sim_time % 3600) // 60)
        seconds = int(sim_time % 60)
        total_generated = sum(stats["generated"].values())
        avg_queue = stats["queued"] / total_generated * 100 if total_generated > 0 else 0

        # Данные отчета
        report_lines = [
            ("⏱ ВРЕМЯ РАБОТЫ", ""),
            (f"Длительность симуляции: {hours:02d}:{minutes:02d}:{seconds:02d}", f"({int(sim_time)} секунд)"),
            (f"Всего циклов обработки:", f"{stats['total_cycles']}"),
            ("", ""),
            ("📊 ГЕНЕРАЦИЯ ДАННЫХ", ""),
            (f"  Датчик 1:", f"{stats['generated'][1]} раз"),
            (f"  Датчик 2:", f"{stats['generated'][2]} раз"),
            (f"  Датчик 3:", f"{stats['generated'][3]} раз"),
            (f"  ВСЕГО:", f"{total_generated} генераций"),
            ("", ""),
            ("✅ ОБРАБОТКА ЗАДАНИЙ", ""),
            (f"Обработано полностью:", f"{stats['processed']}"),
            (f"Отправлено в очередь:", f"{stats['queued']} ({avg_queue:.1f}%)"),
            (f"Осталось в очереди:", f"{len(places['P5'].tokens)}"),
            (f"Макс. размер очереди:", f"{stats['max_queue_size']}"),
            ("", ""),
            ("💻 СТАТИСТИКА ЦИКЛОВ", ""),
            (f"Рабочих циклов:", f"{stats['total_cycles'] - stats['free_cycles']}"),
            (f"Свободных циклов:", f"{stats['free_cycles']}"),
            ("", ""),
            ("📈 ЭФФЕКТИВНОСТЬ", ""),
            (
                f"Среднее время между генерациями:",
                f"~{sim_time/total_generated:.1f} сек" if total_generated > 0 else "N/A",
            ),
            (f"Средний размер данных:", f"~3000 символов"),
            (f"Обработано данных:", f"~{stats['processed'] * 3000 + stats['queued'] * 1500} символов"),
        ]

        y_offset = report_y + 80
        for line_left, line_right in report_lines:
            if line_left == "" and line_right == "":
                y_offset += 5
                continue

            if line_right == "" and line_left != "":
                section_text = title_font.render(line_left, True, (60, 60, 60))
                screen.blit(section_text, (report_x + 40, y_offset))
                y_offset += 35
            else:
                left_text = font.render(line_left, True, TEXT_COLOR)
                screen.blit(left_text, (report_x + 60, y_offset))

                if line_right:
                    right_text = title_font.render(line_right, True, (200, 60, 60))
                    screen.blit(right_text, (report_x + report_width - right_text.get_width() - 60, y_offset))

                y_offset += 25

        button_y = report_y + report_height - 70

        continue_button = pygame.Rect(report_x + 50, button_y, 300, 45)
        pygame.draw.rect(screen, (70, 130, 220), continue_button, border_radius=8)
        pygame.draw.rect(screen, (50, 100, 180), continue_button, 2, border_radius=8)
        continue_text = font.render("Продолжить наблюдение", True, (255, 255, 255))
        screen.blit(
            continue_text,
            (
                continue_button.centerx - continue_text.get_width() // 2,
                continue_button.centery - continue_text.get_height() // 2,
            ),
        )

        close_button = pygame.Rect(report_x + report_width - 350, button_y, 300, 45)
        pygame.draw.rect(screen, (220, 70, 70), close_button, border_radius=8)
        pygame.draw.rect(screen, (180, 50, 50), close_button, 2, border_radius=8)
        close_text = font.render("Закрыть программу (ESC)", True, (255, 255, 255))
        screen.blit(
            close_text,
            (
                close_button.centerx - close_text.get_width() // 2,
                close_button.centery - close_text.get_height() // 2,
            ),
        )

        pygame.display.flip()
        clock.tick(60)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:

                if continue_button.collidepoint(e.pos):
                    simulation_finished = False
                    paused = False
                    add_to_log("▶ Продолжение наблюдения...")

                if close_button.collidepoint(e.pos):
                    running = False

        continue

    arc_connections = [
        (transitions["T1"], places["P1"], 0, False, True),
        (transitions["T2"], places["P2"], 0, False, True),
        (transitions["T3"], places["P3"], 0, False, True),
        (places["P1"], transitions["T4"], 0, True, False),
        (places["P2"], transitions["T5"], 0, True, False),
        (places["P3"], transitions["T6"], 0, True, False),
        (places["P4"], transitions["T4"], 50, True, False),
        (places["P4"], transitions["T5"], 30, True, False),
        (places["P4"], transitions["T6"], 10, True, False),
        (places["P4"], transitions["T10"], 70, True, False),
        (places["P4"], transitions["T11"], 90, True, False),
        (places["P9"], transitions["T4"], -50, True, False),
        (places["P9"], transitions["T5"], -30, True, False),
        (places["P9"], transitions["T6"], -10, True, False),
        (places["P9"], transitions["T10"], -70, True, False),
        (places["P9"], transitions["T11"], -90, True, False),
        (places["P5"], transitions["T10"], 0, True, False),
        (transitions["T10"], places["P6"], 80, False, True, 1.5),
        (transitions["T10"], places["P7"], 40, False, True, 1.5),
        (transitions["T10"], places["P8"], -80, False, True, 1.5),
        (transitions["T4"], places["P6"], 0, False, True),
        (transitions["T5"], places["P7"], 0, False, True),
        (transitions["T6"], places["P8"], 0, False, True),
        (places["P6"], transitions["T7"], 0, True, False),
        (places["P7"], transitions["T8"], 0, True, False),
        (places["P8"], transitions["T9"], 0, True, False),
        (transitions["T7"], places["P4"], 60, False, True),
        (transitions["T7"], places["P9"], 80, False, True),
        (transitions["T8"], places["P4"], 30, False, True),
        (transitions["T8"], places["P9"], 50, False, True),
        (transitions["T9"], places["P4"], -60, False, True),
        (transitions["T9"], places["P9"], -40, False, True),
        (transitions["T11"], places["P9"], 0, False, True),
        (transitions["T11"], places["P4"], 0, False, True),
    ]

    for connection in arc_connections:
        if len(connection) == 6:
            src, dst, curve, src_is_place, dst_is_place, arrow_scale = connection
        else:
            src, dst, curve, src_is_place, dst_is_place = connection
            arrow_scale = 1.0
        draw_curved_arrow(screen, ARC_COLOR, src, dst, 2, curve, src_is_place, dst_is_place, arrow_scale)

    for t in transitions.values():
        border_color = (
            ACTIVE_COLOR if (t.active and time.time() - t.activation_time < 0.5) else TRANSITION_BORDER
        )
        if time.time() - t.activation_time > 0.5:
            t.active = False

        rect = pygame.Rect(t.pos[0] - t.width // 2, t.pos[1] - t.height // 2, t.width, t.height)

        gradient_surf = pygame.Surface((rect.width, rect.height))
        for i in range(rect.height):
            color_ratio = i / rect.height
            r = int(TRANSITION_COLOR[0] * (1 - color_ratio) + 240 * color_ratio)
            g = int(TRANSITION_COLOR[1] * (1 - color_ratio) + 240 * color_ratio)
            b = int(TRANSITION_COLOR[2] * (1 - color_ratio) + 240 * color_ratio)
            pygame.draw.line(gradient_surf, (r, g, b), (0, i), (rect.width, i))
        screen.blit(gradient_surf, rect.topleft)

        # Тень
        shadow_rect = pygame.Rect(rect.x + int(4 * zoom), rect.y + int(4 * zoom), rect.width, rect.height)
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf, (100, 100, 100, 80), shadow_surf.get_rect(), border_radius=int(8 * zoom)
        )
        screen.blit(shadow_surf, shadow_rect)

        if t.active:
            bg_color = (255, 240, 240)
        else:
            bg_color = TRANSITION_COLOR

        if t.active:
            active_gradient = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            for i in range(rect.height):
                alpha = int(50 * (1 - i / rect.height))
                pygame.draw.line(active_gradient, (*ACTIVE_COLOR, alpha), (0, i), (rect.width, i))
            screen.blit(active_gradient, rect.topleft)

        inner_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4)
        pygame.draw.rect(
            screen,
            (240, 240, 240) if not t.active else (255, 230, 230),
            inner_rect,
            max(1, int(1 * zoom)),
            border_radius=int(6 * zoom),
        )

        border_width = max(2, int(4 * zoom)) if t.active else max(1, int(3 * zoom))
        pygame.draw.rect(screen, border_color, rect, border_width, border_radius=int(8 * zoom))

        if zoom > 0.4:
            lines = t.display_name.split("\n")
            text_size = max(12, int(16 * zoom))
            try:
                scaled_font = pygame.font.SysFont("Arial", text_size)
            except:
                scaled_font = pygame.font.Font(None, text_size)

            total_height = len(lines) * text_size * 0.85
            y_start = t.pos[1] - total_height // 2

            for i, line in enumerate(lines):
                text_shadow = scaled_font.render(line, True, (150, 150, 150))
                screen.blit(
                    text_shadow,
                    (t.pos[0] - text_shadow.get_width() / 2 + 1, y_start + i * text_size * 0.85 + 1),
                )
                text_color = ACTIVE_COLOR if (t.active and i == 0) else TEXT_COLOR
                text = scaled_font.render(line, True, text_color)
                screen.blit(text, (t.pos[0] - text.get_width() / 2, y_start + i * text_size * 0.85))

    for p in places.values():
        radius = int(75 * zoom)
        color = PLACE_COLOR

        for i in range(3):
            glow_radius = radius + int((6 - i * 2) * zoom)
            glow_alpha = 40 - i * 10
            glow_color = tuple(min(255, c + 30) for c in color[:3])
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color, glow_alpha), (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (p.pos[0] - glow_radius, p.pos[1] - glow_radius))

        shadow_offset = int(5 * zoom)
        pygame.draw.circle(
            screen, (150, 150, 150, 100), (p.pos[0] + shadow_offset, p.pos[1] + shadow_offset), radius
        )

        light_color = tuple(min(255, c + 40) for c in color)
        for i in range(radius, 0, -max(1, int(radius / 20))):
            ratio = i / radius
            grad_color = tuple(int(color[j] * ratio + light_color[j] * (1 - ratio)) for j in range(3))
            pygame.draw.circle(screen, grad_color, p.pos, i)

        pygame.draw.circle(screen, color, p.pos, radius)

        highlight_pos = (p.pos[0] - int(radius * 0.3), p.pos[1] - int(radius * 0.3))
        highlight_radius = int(radius * 0.3)
        highlight_surf = pygame.Surface((highlight_radius * 2, highlight_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            highlight_surf, (255, 255, 255, 80), (highlight_radius, highlight_radius), highlight_radius
        )
        screen.blit(
            highlight_surf, (highlight_pos[0] - highlight_radius, highlight_pos[1] - highlight_radius)
        )

        pygame.draw.circle(screen, PLACE_BORDER, p.pos, radius, max(2, int(4 * zoom)))

        if zoom > 0.4:
            lines = p.display_name.split("\n")
            text_size = max(14, int(18 * zoom))
            try:
                scaled_font = pygame.font.SysFont("Arial", text_size)
            except:
                scaled_font = pygame.font.Font(None, text_size)

            for i, line in enumerate(lines):
                text_shadow = scaled_font.render(line, True, (100, 100, 100))
                screen.blit(
                    text_shadow,
                    (
                        p.pos[0] - text_shadow.get_width() / 2 + 2,
                        p.pos[1] - radius - int(50 * zoom) + int(i * 18 * zoom) + 2,
                    ),
                )
                text = scaled_font.render(line, True, TEXT_COLOR)
                screen.blit(
                    text,
                    (
                        p.pos[0] - text.get_width() / 2,
                        p.pos[1] - radius - int(50 * zoom) + int(i * 18 * zoom),
                    ),
                )

        value_size = max(22, int(36 * zoom))
        try:
            value_font = pygame.font.SysFont("Arial", value_size)
        except:
            value_font = pygame.font.Font(None, value_size)

        if p.name in ["P1", "P2", "P3", "P5"]:
            num = len(p.tokens)
            shadow = value_font.render(str(num), True, (0, 0, 0))
            screen.blit(
                shadow, (p.pos[0] - shadow.get_width() / 2 + 3, p.pos[1] - shadow.get_height() / 2 + 3)
            )
            text = value_font.render(str(num), True, (255, 255, 255))
            screen.blit(text, (p.pos[0] - text.get_width() / 2, p.pos[1] - text.get_height() / 2))
        elif p.name in ["P6", "P7", "P8"]:
            if p.tokens:
                size_kb = int(p.tokens[0].size / 1000)
                shadow = value_font.render(f"{size_kb}k", True, (0, 0, 0))
                text = value_font.render(f"{size_kb}k", True, (255, 255, 255))
            else:
                shadow = value_font.render("0", True, (0, 0, 0))
                text = value_font.render("0", True, (255, 255, 255))
            screen.blit(
                shadow, (p.pos[0] - shadow.get_width() / 2 + 3, p.pos[1] - shadow.get_height() / 2 + 3)
            )
            screen.blit(text, (p.pos[0] - text.get_width() / 2, p.pos[1] - text.get_height() / 2))
        elif p.name == "P4":
            num = len(p.tokens)
            shadow = value_font.render(str(num), True, (0, 0, 0))
            text = value_font.render(str(num), True, (80, 80, 80))
            screen.blit(
                shadow, (p.pos[0] - shadow.get_width() / 2 + 3, p.pos[1] - shadow.get_height() / 2 + 3)
            )
            screen.blit(text, (p.pos[0] - text.get_width() / 2, p.pos[1] - text.get_height() / 2))
        elif p.name == "P9":
            if p.tokens:
                phase = p.tokens[0].phase
                shadow = value_font.render(str(phase), True, (0, 0, 0))
                text = value_font.render(str(phase), True, (255, 255, 255))
            else:
                shadow = value_font.render("-", True, (0, 0, 0))
                text = value_font.render("-", True, (255, 255, 255))
            screen.blit(
                shadow, (p.pos[0] - shadow.get_width() / 2 + 3, p.pos[1] - shadow.get_height() / 2 + 3)
            )
            screen.blit(text, (p.pos[0] - text.get_width() / 2, p.pos[1] - text.get_height() / 2))

    new_moving = []
    for mt in moving_tokens:
        progress = (time.time() - mt.t_start) / mt.duration

        if progress < 1:
            pos = mt.get_current_pos()
            token_radius = int(14 * zoom)

            glow_surf = pygame.Surface((token_radius * 4, token_radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf, (100, 150, 255, 60), (token_radius * 2, token_radius * 2), token_radius * 2
            )
            screen.blit(glow_surf, (pos[0] - token_radius * 2, pos[1] - token_radius * 2))

            pygame.draw.circle(screen, (100, 100, 100), (pos[0] + 3, pos[1] + 3), token_radius)

            for i in range(token_radius, 0, -max(1, token_radius // 8)):
                ratio = i / token_radius
                color_value = int(30 + (255 - 30) * (1 - ratio))
                pygame.draw.circle(screen, (color_value, color_value, color_value), pos, i)

            pygame.draw.circle(screen, TOKEN_COLOR, pos, token_radius)

            highlight_pos = (pos[0] - token_radius // 3, pos[1] - token_radius // 3)
            pygame.draw.circle(screen, (255, 255, 255), highlight_pos, max(2, token_radius // 4))

            pygame.draw.circle(screen, (255, 255, 255), pos, token_radius, max(1, int(3 * zoom)))
            new_moving.append(mt)
    moving_tokens = new_moving

    if show_legend_panel:
        legend_x = 30
        legend_y = 30
        legend_width = 420
        legend_height = 300

        pygame.draw.rect(
            screen,
            (200, 200, 200),
            (legend_x + 4, legend_y + 4, legend_width, legend_height),
            border_radius=10,
        )
        pygame.draw.rect(
            screen, LEGEND_BG, (legend_x, legend_y, legend_width, legend_height), border_radius=10
        )
        pygame.draw.rect(
            screen, (100, 100, 100), (legend_x, legend_y, legend_width, legend_height), 2, border_radius=10
        )

        title = title_font.render("Легенда", True, TEXT_COLOR)
        screen.blit(title, (legend_x + 15, legend_y + 15))

        legend_items = [
            "Система управления производством",
            "",
            "• Параметры:",
            "  - Период генерации: 12±3 с",
            "  - Размер данных: 3000±1000 символов",
            "  - Время обработки: 3 с на датчик",
            "  - Скорость ЭВМ: 1000 символов/с",
            "",
            "• Позиции (круги):",
            "  P1-P3: Данные от датчиков",
            "  P4: Состояние ЭВМ (1=свободна)",
            "  P5: Очередь необработанных заданий",
            "  P6-P8: Активная обработка (остаток)",
            "  P9: Текущая фаза цикла (0-2)",
        ]

        y_offset = 50
        for item in legend_items:
            if item == "":
                y_offset += 5
                continue
            text = small_font.render(item, True, TEXT_COLOR)
            screen.blit(text, (legend_x + 15, legend_y + y_offset))
            y_offset += 20

    if show_stats_panel:
        stats_x = SCREEN_WIDTH - 430
        stats_y = 30
        stats_width = 400
        stats_height = 220

        pygame.draw.rect(
            screen, (200, 200, 200), (stats_x + 4, stats_y + 4, stats_width, stats_height), border_radius=10
        )
        pygame.draw.rect(screen, LEGEND_BG, (stats_x, stats_y, stats_width, stats_height), border_radius=10)
        pygame.draw.rect(
            screen, (100, 100, 100), (stats_x, stats_y, stats_width, stats_height), 2, border_radius=10
        )

        hours = int(sim_time // 3600)
        minutes = int((sim_time % 3600) // 60)
        seconds = int(sim_time % 60)

        stats_items = [
            f"Время симуляции: {hours:02d}:{minutes:02d}:{seconds:02d}",
            "",
            f"Обработано заданий: {stats['processed']}",
            f"В очереди сейчас: {len(places['P5'].tokens)}",
            f"Макс. размер очереди: {stats['max_queue_size']}",
            f"Отправлено в очередь: {stats['queued']}",
            f"Свободных циклов: {stats['free_cycles']}",
            f"Всего циклов: {stats['total_cycles']}",
            "",
            f"Скорость: {speed}x {'⏸ ПАУЗА' if paused else ''}",
        ]

        y_offset = 15
        for item in stats_items:
            if item == "":
                y_offset += 8
                continue
            if "Время симуляции" in item:
                text = title_font.render(item, True, TEXT_COLOR)
            else:
                text = font.render(item, True, TEXT_COLOR)
            screen.blit(text, (stats_x + 15, stats_y + y_offset))
            y_offset += 20

        log_x = SCREEN_WIDTH - 430
        log_y = 270
        log_width = 400
        log_height = SCREEN_HEIGHT - 400

        pygame.draw.rect(
            screen, (200, 200, 200), (log_x + 4, log_y + 4, log_width, log_height), border_radius=10
        )
        pygame.draw.rect(screen, LEGEND_BG, (log_x, log_y, log_width, log_height), border_radius=10)
        pygame.draw.rect(screen, (100, 100, 100), (log_x, log_y, log_width, log_height), 2, border_radius=10)

        log_title = title_font.render("События и переходы", True, TEXT_COLOR)
        screen.blit(log_title, (log_x + 15, log_y + 15))

        y_offset = 50
        max_events = (log_height - 80) // 24
        for timestamp, message in event_log[-max_events:]:
            time_text = tiny_font.render(timestamp, True, (100, 100, 100))
            screen.blit(time_text, (log_x + 15, log_y + y_offset))

            msg_text = tiny_font.render(message[:45], True, TEXT_COLOR)
            screen.blit(msg_text, (log_x + 85, log_y + y_offset))
            y_offset += 24

    control_panel_height = 60
    control_y = SCREEN_HEIGHT - control_panel_height

    pygame.draw.rect(screen, LEGEND_BG, (0, control_y, SCREEN_WIDTH, control_panel_height))
    pygame.draw.rect(screen, (100, 100, 100), (0, control_y, SCREEN_WIDTH, 2))

    controls_text = [
        "🖱️ Колесо - Масштаб | ЛКМ + перетаскивание - Перемещение | Пробел - Пауза | +/- Скорость | R - Сброс камеры",
        f"📊 Масштаб: {int(zoom * 100)}% | Камера: X={int(camera_x)}, Y={int(camera_y)} | L - Легенда | S - Статистика | ESC - Выход",
    ]

    y_pos = control_y + 10
    for text_line in controls_text:
        text = small_font.render(text_line, True, TEXT_COLOR)
        screen.blit(text, (30, y_pos))
        y_pos += 22

    exit_button = pygame.Rect(SCREEN_WIDTH - 150, control_y + 10, 120, 40)
    pygame.draw.rect(screen, (220, 53, 69), exit_button, border_radius=8)
    pygame.draw.rect(screen, (180, 40, 55), exit_button, 2, border_radius=8)
    exit_text = font.render("Выход (ESC)", True, (255, 255, 255))
    screen.blit(
        exit_text,
        (exit_button.centerx - exit_text.get_width() / 2, exit_button.centery - exit_text.get_height() / 2),
    )

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            elif e.key == pygame.K_SPACE and not simulation_finished:
                paused = not paused
                add_to_log("⏸ Пауза" if paused else "▶ Продолжить")
            elif e.key == pygame.K_r:
                camera_x = 0
                camera_y = 0
                zoom = 0.7
                add_to_log("🎥 Камера сброшена")
            elif e.key == pygame.K_l:
                show_legend_panel = not show_legend_panel
            elif e.key == pygame.K_s:
                show_stats_panel = not show_stats_panel
            elif e.key == pygame.K_PLUS or e.key == pygame.K_EQUALS:
                speed = min(100, speed + 5)
                add_to_log(f"⚡ Скорость: {speed}x")
            elif e.key == pygame.K_MINUS:
                speed = max(1, speed - 5)
                add_to_log(f"⚡ Скорость: {speed}x")
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if "exit_button" in locals() and exit_button.collidepoint(e.pos):
                running = False
            elif e.button == 1:
                dragging = True
                last_mouse_pos = e.pos
            elif e.button == 4:
                old_zoom = zoom
                zoom = min(max_zoom, zoom * 1.1)
                mouse_x, mouse_y = e.pos
                camera_x = (
                    camera_x + (mouse_x - SCREEN_WIDTH / 2) / old_zoom - (mouse_x - SCREEN_WIDTH / 2) / zoom
                )
                camera_y = (
                    camera_y + (mouse_y - SCREEN_HEIGHT / 2) / old_zoom - (mouse_y - SCREEN_HEIGHT / 2) / zoom
                )
            elif e.button == 5:
                old_zoom = zoom
                zoom = max(min_zoom, zoom / 1.1)
                mouse_x, mouse_y = e.pos
                camera_x = (
                    camera_x + (mouse_x - SCREEN_WIDTH / 2) / old_zoom - (mouse_x - SCREEN_WIDTH / 2) / zoom
                )
                camera_y = (
                    camera_y + (mouse_y - SCREEN_HEIGHT / 2) / old_zoom - (mouse_y - SCREEN_HEIGHT / 2) / zoom
                )
        elif e.type == pygame.MOUSEBUTTONUP:
            if e.button == 1:
                dragging = False
        elif e.type == pygame.MOUSEMOTION:
            if dragging:
                dx = e.pos[0] - last_mouse_pos[0]
                dy = e.pos[1] - last_mouse_pos[1]
                camera_x += dx / zoom
                camera_y += dy / zoom
                last_mouse_pos = e.pos

    pygame.display.flip()
    clock.tick(60)

print("\n" + "=" * 60)
print("ИТОГОВАЯ СТАТИСТИКА СИМУЛЯЦИИ")
print("=" * 60)
print(f"Время симуляции: {sim_time/3600:.2f} часов ({int(sim_time)} секунд)")
print(f"Всего циклов обработки: {stats['total_cycles']}")
print("-" * 60)
print(f"Сгенерировано данных:")
print(f"  - Датчик 1: {stats['generated'][1]} раз")
print(f"  - Датчик 2: {stats['generated'][2]} раз")
print(f"  - Датчик 3: {stats['generated'][3]} раз")
print(f"  - Всего: {sum(stats['generated'].values())} генераций")
print("-" * 60)
print(f"Обработано заданий полностью: {stats['processed']}")
print(f"Отправлено в очередь: {stats['queued']}")
print(f"Осталось в очереди: {len(places['P5'].tokens)}")
print(f"Максимальный размер очереди: {stats['max_queue_size']}")
print("-" * 60)
print(f"Свободных циклов: {stats['free_cycles']}")
print("=" * 60)

pygame.quit()
