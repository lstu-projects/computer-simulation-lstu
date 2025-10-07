# ui_mixins.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QTableWidget, QTableWidgetItem, QTabWidget, QGridLayout,
                             QGroupBox, QMessageBox, QSpinBox, QSlider, QComboBox, QFileDialog, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class UIMixin:
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Создаем вкладки
        tab_widget = QTabWidget()
        
        # Вкладка ввода данных
        input_tab = self.create_input_tab()
        tab_widget.addTab(input_tab, "Ввод данных")
        
        # Вкладка матричного анализа
        matrix_tab = self.create_matrix_analysis_tab()
        tab_widget.addTab(matrix_tab, "Матричный анализ")
        
        # Вкладка дерева достижимости
        tree_tab = self.create_reachability_tree_tab()
        tab_widget.addTab(tree_tab, "Дерево достижимости")
        
        # Вкладка визуализации
        visual_tab = self.create_visualization_tab()
        tab_widget.addTab(visual_tab, "Визуализация")
        
        layout = QVBoxLayout()
        layout.addWidget(tab_widget)
        central_widget.setLayout(layout)
        
    def create_input_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Размерность сети
        size_group = QGroupBox("Размерность сети")
        size_layout = QGridLayout()
        
        size_layout.addWidget(QLabel("Количество позиций:"), 0, 0)
        self.positions_spin = QSpinBox()
        self.positions_spin.setMinimum(1)
        self.positions_spin.setMaximum(20)
        self.positions_spin.setValue(4)
        size_layout.addWidget(self.positions_spin, 0, 1)
        
        size_layout.addWidget(QLabel("Количество переходов:"), 0, 2)
        self.transitions_spin = QSpinBox()
        self.transitions_spin.setMinimum(1)
        self.transitions_spin.setMaximum(20)
        self.transitions_spin.setValue(4)
        size_layout.addWidget(self.transitions_spin, 0, 3)
        
        create_matrices_btn = QPushButton("Создать матрицы")
        create_matrices_btn.clicked.connect(self.create_matrices)
        size_layout.addWidget(create_matrices_btn, 0, 4)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # Матрицы
        matrices_group = QGroupBox("Матрицы сети Петри")
        matrices_layout = QHBoxLayout()
        
        # Матрица F
        f_layout = QVBoxLayout()
        f_layout.addWidget(QLabel("Матрица входов F (P×T):"))
        self.f_table = QTableWidget()
        f_layout.addWidget(self.f_table)
        matrices_layout.addLayout(f_layout)
        
        # Матрица H
        h_layout = QVBoxLayout()
        h_layout.addWidget(QLabel("Матрица выходов H (T×P):"))
        self.h_table = QTableWidget()
        h_layout.addWidget(self.h_table)
        matrices_layout.addLayout(h_layout)
        
        # Начальная разметка
        m0_layout = QVBoxLayout()
        m0_layout.addWidget(QLabel("Начальная разметка M0:"))
        self.m0_table = QTableWidget()
        m0_layout.addWidget(self.m0_table)
        matrices_layout.addLayout(m0_layout)
        
        matrices_group.setLayout(matrices_layout)
        layout.addWidget(matrices_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        load_example_btn = QPushButton("Загрузить пример (Вариант 2)")
        load_example_btn.clicked.connect(self.load_example)
        buttons_layout.addWidget(load_example_btn)
        
        load_file_btn = QPushButton("Загрузить из файла")
        load_file_btn.clicked.connect(self.load_from_file)
        buttons_layout.addWidget(load_file_btn)
        
        save_file_btn = QPushButton("Сохранить в файл")
        save_file_btn.clicked.connect(self.save_to_file)
        buttons_layout.addWidget(save_file_btn)
        
        analyze_btn = QPushButton("Анализировать сеть")
        analyze_btn.clicked.connect(self.analyze_network)
        buttons_layout.addWidget(analyze_btn)
        
        layout.addLayout(buttons_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_matrix_analysis_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Результаты матричного анализа
        self.matrix_results = QTextEdit()
        self.matrix_results.setReadOnly(True)
        self.matrix_results.setFont(QFont("Consolas", 10))
        layout.addWidget(QLabel("Результаты матричного анализа:"))
        layout.addWidget(self.matrix_results)
        
        widget.setLayout(layout)
        return widget
    
    def create_reachability_tree_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        build_tree_btn = QPushButton("Построить дерево достижимости")
        build_tree_btn.clicked.connect(self.build_and_visualize_reachability_tree)
        layout.addWidget(build_tree_btn)
        
        # Splitter для текста и графа
        splitter = QSplitter(Qt.Horizontal)
        
        # Текст слева
        text_widget = QWidget()
        text_layout = QVBoxLayout()
        text_layout.addWidget(QLabel("Дерево достижимых разметок:"))
        self.tree_results = QTextEdit()
        self.tree_results.setReadOnly(True)
        self.tree_results.setFont(QFont("Consolas", 10))
        text_layout.addWidget(self.tree_results)
        text_widget.setLayout(text_layout)
        splitter.addWidget(text_widget)
        
        # Граф справа
        self.tree_figure = Figure(figsize=(12, 8))
        self.tree_canvas = FigureCanvas(self.tree_figure)
        splitter.addWidget(self.tree_canvas)
        
        layout.addWidget(splitter)
        
        widget.setLayout(layout)
        return widget
    
    def create_visualization_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Элементы управления анимацией
        controls_group = QGroupBox("Управление анимацией")
        controls_layout = QGridLayout()
        
        # Кнопки управления
        self.start_animation_btn = QPushButton("Запустить анимацию")
        self.start_animation_btn.clicked.connect(self.start_animation)
        controls_layout.addWidget(self.start_animation_btn, 0, 0)
        
        self.stop_animation_btn = QPushButton("Остановить")
        self.stop_animation_btn.clicked.connect(self.stop_animation)
        self.stop_animation_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_animation_btn, 0, 1)
        
        self.reset_animation_btn = QPushButton("Сброс")
        self.reset_animation_btn.clicked.connect(self.reset_animation)
        controls_layout.addWidget(self.reset_animation_btn, 0, 2)
        
        # Выбор перехода для срабатывания
        controls_layout.addWidget(QLabel("Переход:"), 1, 0)
        self.transition_combo = QComboBox()
        self.transition_combo.addItem("Автоматический выбор")
        controls_layout.addWidget(self.transition_combo, 1, 1)
        
        self.fire_transition_btn = QPushButton("Сработать")
        self.fire_transition_btn.clicked.connect(self.fire_selected_transition)
        controls_layout.addWidget(self.fire_transition_btn, 1, 2)
        
        # Скорость анимации
        controls_layout.addWidget(QLabel("Скорость:"), 2, 0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(3000)
        self.speed_slider.setValue(1000)
        self.speed_slider.valueChanged.connect(self.change_animation_speed)
        controls_layout.addWidget(self.speed_slider, 2, 1)
        
        self.speed_label = QLabel("1.0s")
        controls_layout.addWidget(self.speed_label, 2, 2)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Информация о текущем состоянии
        info_group = QGroupBox("Текущее состояние")
        info_layout = QVBoxLayout()
        
        self.current_state_label = QLabel("Текущая разметка: не инициализирована")
        self.current_state_label.setFont(QFont("Consolas", 10))
        info_layout.addWidget(self.current_state_label)
        
        self.enabled_transitions_label = QLabel("Разрешенные переходы: нет")
        self.enabled_transitions_label.setFont(QFont("Consolas", 10))
        info_layout.addWidget(self.enabled_transitions_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Matplotlib canvas для визуализации
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        visualize_btn = QPushButton("Инициализировать визуализацию")
        visualize_btn.clicked.connect(self.initialize_visualization)
        layout.addWidget(visualize_btn)
        
        widget.setLayout(layout)
        return widget