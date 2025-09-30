from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import sys

from ui_mixins import UIMixin
from data_mixins import DataMixin
from analysis_mixins import AnalysisMixin
from animation_mixins import AnimationMixin
from visualization_mixins import VisualizationMixin


class PetriNetAnalyzer(QMainWindow, UIMixin, DataMixin, AnalysisMixin, AnimationMixin, VisualizationMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализатор сетей Петри")
        self.setGeometry(100, 100, 1200, 800)

        self.F = None  # Матрица входов
        self.H = None  # Матрица выходов
        self.M0 = None  # Начальная разметка
        self.C = None  # Матрица инцидентности

        self.current_marking = None
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animation_step)
        self.animation_running = False
        self.animation_speed = 1000
        self.reachable_markings = []
        self.current_animation_step = 0
        self.ani = None

        self.init_ui()


def main():
    app = QApplication(sys.argv)
    window = PetriNetAnalyzer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
