"""
Программа для генерации псевдослучайных чисел с равномерным распределением
и случайных величин с заданным распределением
"""

import sys
import numpy as np
from scipy import stats
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QGridLayout,
    QFrame,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QDialog,
    QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class MRG2Generator:
    """
    Комбинированный генератор случайных чисел
    Использует два мультипликативных линейных конгруэнтных генератора
    """

    def __init__(self, seed1=12345, seed2=67890):
        self.m1 = 2147483563
        self.a1 = 40014
        self.m2 = 2147483399
        self.a2 = 40692

        self.state1 = seed1 % self.m1
        self.state2 = seed2 % self.m2

        if self.state1 == 0:
            self.state1 = 1
        if self.state2 == 0:
            self.state2 = 1

    def next(self):
        self.state1 = (self.a1 * self.state1) % self.m1
        self.state2 = (self.a2 * self.state2) % self.m2
        z = (self.state1 - self.state2) % (self.m1 - 1)
        return z / self.m1
    
    def generate_sample(self, n):
        return np.array([self.next() for _ in range(n)])


class NormalDistributionGenerator:
    """
    Генератор случайных величин с нормальным распределением N(μ, σ²)
    Используется метод Бокса-Мюллера
    """

    def __init__(self, rng_generator, mu=1.0, sigma_squared=0.7):
        self.rng = rng_generator
        self.mu = mu
        self.sigma = np.sqrt(sigma_squared)

    def generate_sample(self, n):
        """Генерация выборки методом Бокса-Мюллера"""
        uniform_sample = self.rng.generate_sample(n * 2)

        result = []
        for i in range(0, len(uniform_sample) - 1, 2):
            u1 = uniform_sample[i]
            u2 = uniform_sample[i + 1]

            if u1 <= 0:
                u1 = 1e-10

            z0 = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
            x = self.mu + self.sigma * z0
            result.append(x)

            if len(result) >= n:
                break

        return np.array(result[:n])


class CustomDistributionGenerator:
    """
    Генератор случайных величин с заданным распределением
    F(x) = sqrt(x) для x ∈ [0; 0.25)
    F(x) = 0.25x + 0.4375 для x ∈ [0.25; 2.25]
    """

    def __init__(self, rng_generator):
        self.rng = rng_generator

    def inverse_cdf(self, u):
        if u < 0.5:
            return u**2
        else:
            return (u - 0.4375) / 0.25

    def generate_sample(self, n):
        uniform_sample = self.rng.generate_sample(n)
        return np.array([self.inverse_cdf(u) for u in uniform_sample])

    @staticmethod
    def pdf(x):
        if 0 <= x < 0.25:
            return 1 / (2 * np.sqrt(x)) if x > 0 else np.inf
        elif 0.25 <= x <= 2.25:
            return 0.25
        else:
            return 0

    @staticmethod
    def cdf(x):
        if x < 0:
            return 0
        elif x < 0.25:
            return np.sqrt(x)
        elif x <= 2.25:
            return 0.25 * x + 0.4375
        else:
            return 1

    @staticmethod
    def theoretical_mean():
        part1 = (1 / 3) * (0.25**1.5)
        part2 = 0.25 * ((2.25**2 - 0.25**2) / 2)
        return part1 + part2

    @staticmethod
    def theoretical_variance():
        part1 = (1 / 5) * (0.25**2.5)
        part2 = 0.25 * ((2.25**3 - 0.25**3) / 3)
        ex2 = part1 + part2
        ex = CustomDistributionGenerator.theoretical_mean()
        return ex2 - ex**2


class StatisticsAnalyzer:
    """Класс для статистического анализа выборки"""

    @staticmethod
    def calculate_statistics(sample):
        mean = np.mean(sample)
        variance = np.var(sample, ddof=1)
        std = np.std(sample, ddof=1)

        return {"mean": mean, "variance": variance, "std": std, "min": np.min(sample), "max": np.max(sample)}

    @staticmethod
    def chi_square_test(
        sample,
        num_bins=16,
        alpha=0.05,
        distribution="uniform",
        theoretical_cdf=None,
        mu=None,
        sigma_squared=None,
    ):
        n = len(sample)

        if distribution == "uniform":
            observed_freq, bin_edges = np.histogram(sample, bins=num_bins, range=(0, 1))
            expected_freq_array = np.full(num_bins, n / num_bins)
        elif distribution == "normal":
            min_val = mu - 4 * np.sqrt(sigma_squared)
            max_val = mu + 4 * np.sqrt(sigma_squared)
            observed_freq, bin_edges = np.histogram(sample, bins=num_bins, range=(min_val, max_val))

            expected_freq_array = []
            for i in range(num_bins):
                p = stats.norm.cdf(bin_edges[i + 1], mu, np.sqrt(sigma_squared)) - stats.norm.cdf(
                    bin_edges[i], mu, np.sqrt(sigma_squared)
                )
                expected_freq_array.append(n * p)
            expected_freq_array = np.array(expected_freq_array)
        else:
            min_val, max_val = np.min(sample), np.max(sample)
            observed_freq, bin_edges = np.histogram(sample, bins=num_bins, range=(min_val, max_val))

            expected_freq_array = []
            for i in range(num_bins):
                p = theoretical_cdf(bin_edges[i + 1]) - theoretical_cdf(bin_edges[i])
                expected_freq_array.append(n * p)
            expected_freq_array = np.array(expected_freq_array)

        mask = expected_freq_array >= 5
        observed_freq_filtered = observed_freq[mask]
        expected_freq_filtered = expected_freq_array[mask]

        if len(observed_freq_filtered) == 0:
            return None

        chi_square_stat = np.sum(
            (observed_freq_filtered - expected_freq_filtered) ** 2 / expected_freq_filtered
        )
        degrees_of_freedom = len(observed_freq_filtered) - 1
        critical_value = stats.chi2.ppf(1 - alpha, degrees_of_freedom)
        hypothesis_accepted = chi_square_stat < critical_value
        p_value = 1 - stats.chi2.cdf(chi_square_stat, degrees_of_freedom)

        return {
            "chi_square": chi_square_stat,
            "critical_value": critical_value,
            "degrees_of_freedom": degrees_of_freedom,
            "p_value": p_value,
            "hypothesis_accepted": hypothesis_accepted,
            "observed_freq": observed_freq,
            "expected_freq": expected_freq_array,
            "bin_edges": bin_edges,
        }

    @staticmethod
    def kolmogorov_test(sample, theoretical_cdf, alpha=0.05):
        n = len(sample)
        sorted_sample = np.sort(sample)

        empirical_cdf = np.arange(1, n + 1) / n
        theoretical_values = np.array([theoretical_cdf(x) for x in sorted_sample])

        d_plus = np.max(empirical_cdf - theoretical_values)
        d_minus = np.max(theoretical_values - (np.arange(0, n) / n))
        d_stat = max(d_plus, d_minus)

        critical_value = 1.36 / np.sqrt(n)
        hypothesis_accepted = d_stat < critical_value

        return {
            "d_statistic": d_stat,
            "critical_value": critical_value,
            "hypothesis_accepted": hypothesis_accepted,
            "d_plus": d_plus,
            "d_minus": d_minus,
        }


class ModernLineEdit(QLineEdit):

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(
            """
            QLineEdit {
                padding: 10px 15px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 13px;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
                background-color: #FAFAFA;
            }
            QLineEdit:hover {
                border: 2px solid #BDBDBD;
            }
        """
        )


class ModernComboBox(QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            """
            QComboBox {
                padding: 10px 15px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 13px;
                color: #333333;
            }
            QComboBox:hover {
                border: 2px solid #BDBDBD;
            }
            QComboBox:focus {
                border: 2px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #666;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
                selection-background-color: #E3F2FD;
                selection-color: #2196F3;
                padding: 5px;
            }
        """
        )


class ModernButton(QPushButton):

    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)

        if primary:
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 12px 20px;
                    font-size: 13px;
                    font-weight: 600;
                    border: none;
                    border-radius: 6px;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #1565C0;
                }
                QPushButton:disabled {
                    background-color: #BDBDBD;
                }
            """
            )
        else:
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: #FFFFFF;
                    color: #2196F3;
                    padding: 12px 20px;
                    font-size: 13px;
                    font-weight: 600;
                    border: 2px solid #2196F3;
                    border-radius: 6px;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: #E3F2FD;
                }
                QPushButton:pressed {
                    background-color: #BBDEFB;
                }
            """
            )


class ModernGroupBox(QGroupBox):
    """Современная группа с улучшенным стилем"""

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(
            """
            QGroupBox {
                font-size: 15px;
                font-weight: 600;
                color: #424242;
                border: 2px solid #E0E0E0;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 20px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 10px;
                background-color: #FFFFFF;
                border-radius: 6px;
            }
        """
        )


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None):
        plt.style.use("seaborn-v0_8-whitegrid")

        fig = Figure(figsize=(10, 7.5), dpi=100, facecolor="white")
        self.axes1 = fig.add_subplot(211)
        self.axes2 = fig.add_subplot(212)

        super().__init__(fig)
        self.setParent(parent)

        fig.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.08, hspace=0.35)

    def plot_uniform_data(self, sample, num_bins=16):
        self.axes1.clear()
        self.axes2.clear()

        primary_color = "#2196F3"
        secondary_color = "#FF5722"

        counts, bins, patches = self.axes1.hist(
            sample,
            bins=num_bins,
            range=(0, 1),
            density=True,
            alpha=0.75,
            color=primary_color,
            edgecolor="white",
            linewidth=1.5,
            label="Наблюдаемая",
        )

        for i, patch in enumerate(patches):
            patch.set_facecolor(primary_color)
            patch.set_alpha(0.7)

        self.axes1.axhline(
            y=1.0,
            color=secondary_color,
            linestyle="--",
            linewidth=2.5,
            label="Теоретическая U(0,1)",
            alpha=0.8,
        )

        self.axes1.set_xlabel("Значение", fontsize=9, fontweight="500", color="#424242")
        self.axes1.set_ylabel("Плотность", fontsize=9, fontweight="500", color="#424242")
        self.axes1.set_title(
            "Гистограмма распределения частот", fontsize=10, fontweight="600", color="#212121", pad=8
        )

        legend1 = self.axes1.legend(fontsize=8, frameon=True, shadow=False, fancybox=True, loc="upper right")
        legend1.get_frame().set_alpha(0.9)

        self.axes1.grid(True, alpha=0.25, linestyle="-", linewidth=0.5)
        self.axes1.set_facecolor("#FAFAFA")
        self.axes1.spines["top"].set_visible(False)
        self.axes1.spines["right"].set_visible(False)
        self.axes1.tick_params(axis="both", which="major", labelsize=8)

        sorted_sample = np.sort(sample)
        y_values = np.arange(1, len(sorted_sample) + 1) / len(sorted_sample)

        self.axes2.plot(
            sorted_sample, y_values, color=primary_color, linewidth=2.5, label="Эмпирическая", alpha=0.9
        )

        x_theory = np.linspace(0, 1, 100)
        y_theory = x_theory
        self.axes2.plot(
            x_theory,
            y_theory,
            color=secondary_color,
            linestyle="--",
            linewidth=2.5,
            label="Теоретическая U(0,1)",
            alpha=0.8,
        )

        self.axes2.set_xlabel("Значение", fontsize=9, fontweight="500", color="#424242")
        self.axes2.set_ylabel("F(x)", fontsize=9, fontweight="500", color="#424242")
        self.axes2.set_title("Функция распределения", fontsize=10, fontweight="600", color="#212121", pad=8)

        legend2 = self.axes2.legend(fontsize=8, frameon=True, shadow=False, fancybox=True, loc="lower right")
        legend2.get_frame().set_alpha(0.9)

        self.axes2.grid(True, alpha=0.25, linestyle="-", linewidth=0.5)
        self.axes2.set_xlim(-0.02, 1.02)
        self.axes2.set_ylim(-0.02, 1.02)
        self.axes2.set_facecolor("#FAFAFA")
        self.axes2.spines["top"].set_visible(False)
        self.axes2.spines["right"].set_visible(False)
        self.axes2.tick_params(axis="both", which="major", labelsize=8)

        self.draw()

    def plot_custom_data(self, sample, num_bins=15):
        self.axes1.clear()
        self.axes2.clear()

        primary_color = "#4CAF50"
        secondary_color = "#FF5722"

        min_val, max_val = 0, 2.25
        counts, bins, patches = self.axes1.hist(
            sample,
            bins=num_bins,
            range=(min_val, max_val),
            density=True,
            alpha=0.75,
            color=primary_color,
            edgecolor="white",
            linewidth=1.5,
            label="Наблюдаемая",
        )

        for patch in patches:
            patch.set_alpha(0.7)

        x_vals = np.linspace(0.001, 2.25, 1000)
        y_vals = [CustomDistributionGenerator.pdf(x) for x in x_vals]
        self.axes1.plot(
            x_vals,
            y_vals,
            color=secondary_color,
            linestyle="--",
            linewidth=2.5,
            label="Теоретическая",
            alpha=0.8,
        )

        self.axes1.set_xlabel("Значение", fontsize=9, fontweight="500", color="#424242")
        self.axes1.set_ylabel("Плотность", fontsize=9, fontweight="500", color="#424242")
        self.axes1.set_title(
            "Гистограмма распределения частот", fontsize=10, fontweight="600", color="#212121", pad=8
        )
        self.axes1.set_xlim(0, 2.3)
        self.axes1.set_ylim(0, max(y_vals) * 1.1)

        legend1 = self.axes1.legend(fontsize=8, frameon=True, shadow=False, fancybox=True, loc="upper right")
        legend1.get_frame().set_alpha(0.9)

        self.axes1.grid(True, alpha=0.25, linestyle="-", linewidth=0.5)
        self.axes1.set_facecolor("#FAFAFA")
        self.axes1.spines["top"].set_visible(False)
        self.axes1.spines["right"].set_visible(False)
        self.axes1.tick_params(axis="both", which="major", labelsize=8)

        sorted_sample = np.sort(sample)
        y_empirical = np.arange(1, len(sorted_sample) + 1) / len(sorted_sample)

        self.axes2.plot(
            sorted_sample, y_empirical, color=primary_color, linewidth=2.5, label="Эмпирическая", alpha=0.9
        )

        x_theory = np.linspace(0, 2.25, 1000)
        y_theory = [CustomDistributionGenerator.cdf(x) for x in x_theory]
        self.axes2.plot(
            x_theory,
            y_theory,
            color=secondary_color,
            linestyle="--",
            linewidth=2.5,
            label="Теоретическая",
            alpha=0.8,
        )

        self.axes2.set_xlabel("Значение", fontsize=9, fontweight="500", color="#424242")
        self.axes2.set_ylabel("F(x)", fontsize=9, fontweight="500", color="#424242")
        self.axes2.set_title("Функция распределения", fontsize=10, fontweight="600", color="#212121", pad=8)
        self.axes2.set_xlim(0, 2.3)
        self.axes2.set_ylim(-0.02, 1.02)

        legend2 = self.axes2.legend(fontsize=8, frameon=True, shadow=False, fancybox=True, loc="lower right")
        legend2.get_frame().set_alpha(0.9)

        self.axes2.grid(True, alpha=0.25, linestyle="-", linewidth=0.5)
        self.axes2.set_facecolor("#FAFAFA")
        self.axes2.spines["top"].set_visible(False)
        self.axes2.spines["right"].set_visible(False)
        self.axes2.tick_params(axis="both", which="major", labelsize=8)

        self.draw()

    def plot_normal_data(self, sample, mu, sigma_squared, num_bins=15):
        self.axes1.clear()
        self.axes2.clear()

        primary_color = "#9C27B0"
        secondary_color = "#FF5722"

        sigma = np.sqrt(sigma_squared)
        min_val = mu - 4 * sigma
        max_val = mu + 4 * sigma

        counts, bins, patches = self.axes1.hist(
            sample,
            bins=num_bins,
            range=(min_val, max_val),
            density=True,
            alpha=0.75,
            color=primary_color,
            edgecolor="white",
            linewidth=1.5,
            label="Наблюдаемая",
        )

        for patch in patches:
            patch.set_alpha(0.7)

        x_vals = np.linspace(min_val, max_val, 1000)
        y_vals = stats.norm.pdf(x_vals, mu, sigma)
        self.axes1.plot(
            x_vals,
            y_vals,
            color=secondary_color,
            linestyle="--",
            linewidth=2.5,
            label=f"Теоретическая N({mu}, {sigma_squared})",
            alpha=0.8,
        )

        self.axes1.set_xlabel("Значение", fontsize=9, fontweight="500", color="#424242")
        self.axes1.set_ylabel("Плотность", fontsize=9, fontweight="500", color="#424242")
        self.axes1.set_title(
            "Гистограмма распределения частот", fontsize=10, fontweight="600", color="#212121", pad=8
        )

        legend1 = self.axes1.legend(fontsize=8, frameon=True, shadow=False, fancybox=True, loc="upper right")
        legend1.get_frame().set_alpha(0.9)

        self.axes1.grid(True, alpha=0.25, linestyle="-", linewidth=0.5)
        self.axes1.set_facecolor("#FAFAFA")
        self.axes1.spines["top"].set_visible(False)
        self.axes1.spines["right"].set_visible(False)
        self.axes1.tick_params(axis="both", which="major", labelsize=8)

        sorted_sample = np.sort(sample)
        y_empirical = np.arange(1, len(sorted_sample) + 1) / len(sorted_sample)

        self.axes2.plot(
            sorted_sample, y_empirical, color=primary_color, linewidth=2.5, label="Эмпирическая", alpha=0.9
        )

        x_theory = np.linspace(min_val, max_val, 1000)
        y_theory = stats.norm.cdf(x_theory, mu, sigma)
        self.axes2.plot(
            x_theory,
            y_theory,
            color=secondary_color,
            linestyle="--",
            linewidth=2.5,
            label=f"Теоретическая N({mu}, {sigma_squared})",
            alpha=0.8,
        )

        self.axes2.set_xlabel("Значение", fontsize=9, fontweight="500", color="#424242")
        self.axes2.set_ylabel("F(x)", fontsize=9, fontweight="500", color="#424242")
        self.axes2.set_title("Функция распределения", fontsize=10, fontweight="600", color="#212121", pad=8)
        self.axes2.set_ylim(-0.02, 1.02)

        legend2 = self.axes2.legend(fontsize=8, frameon=True, shadow=False, fancybox=True, loc="lower right")
        legend2.get_frame().set_alpha(0.9)

        self.axes2.grid(True, alpha=0.25, linestyle="-", linewidth=0.5)
        self.axes2.set_facecolor("#FAFAFA")
        self.axes2.spines["top"].set_visible(False)
        self.axes2.spines["right"].set_visible(False)
        self.axes2.tick_params(axis="both", which="major", labelsize=8)

        self.draw()


class ResultsDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Результаты статистического анализа")
        self.setGeometry(200, 100, 900, 700)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel("Детальные результаты анализа")
        header.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #212121;
                padding: 15px;
                background-color: #E3F2FD;
                border-radius: 8px;
            }
        """
        )
        layout.addWidget(header)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet(
            """
            QTextEdit {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                background-color: #F5F5F5;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 15px;
                line-height: 1.6;
            }
        """
        )
        layout.addWidget(self.results_text)

        close_btn = ModernButton("Закрыть", primary=False)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def set_results(self, html_content):
        self.results_text.setHtml(html_content)


class UniformGeneratorTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_dialog = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        params_group = self._create_params_group()
        left_layout.addWidget(params_group)

        self.generate_btn = ModernButton("Сгенерировать", primary=True)
        self.generate_btn.clicked.connect(self.generate_and_analyze)
        left_layout.addWidget(self.generate_btn)

        self.results_btn = ModernButton("Показать результаты", primary=False)
        self.results_btn.clicked.connect(self.show_results)
        self.results_btn.setEnabled(False)
        left_layout.addWidget(self.results_btn)

        self.reset_btn = ModernButton("Сброс", primary=False)
        self.reset_btn.clicked.connect(self.reset_parameters)
        left_layout.addWidget(self.reset_btn)

        left_layout.addStretch()

        self.plot_canvas = PlotCanvas(self)

        layout.addWidget(left_widget, 1)
        layout.addWidget(self.plot_canvas, 2)

    def _create_params_group(self):
        group = ModernGroupBox("Параметры")
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        label_style = """
            QLabel {
                font-size: 13px;
                color: #616161;
                font-weight: 500;
            }
        """

        label1 = QLabel("Начальное значение y₁(0):")
        label1.setStyleSheet(label_style)
        layout.addWidget(label1, 0, 0)
        self.seed1_input = ModernLineEdit("12345")
        layout.addWidget(self.seed1_input, 0, 1)

        label2 = QLabel("Начальное значение y₂(0):")
        label2.setStyleSheet(label_style)
        layout.addWidget(label2, 1, 0)
        self.seed2_input = ModernLineEdit("67890")
        layout.addWidget(self.seed2_input, 1, 1)

        label3 = QLabel("Объем выборки:")
        label3.setStyleSheet(label_style)
        layout.addWidget(label3, 2, 0)
        self.sample_size_input = ModernLineEdit("2000")
        layout.addWidget(self.sample_size_input, 2, 1)

        label4 = QLabel("Число участков разбиения:")
        label4.setStyleSheet(label_style)
        layout.addWidget(label4, 3, 0)
        self.num_bins_input = ModernLineEdit("16")
        layout.addWidget(self.num_bins_input, 3, 1)

        label5 = QLabel("Уровень значимости α:")
        label5.setStyleSheet(label_style)
        layout.addWidget(label5, 4, 0)
        self.alpha_input = ModernLineEdit("0.05")
        layout.addWidget(self.alpha_input, 4, 1)

        group.setLayout(layout)
        return group

    def reset_parameters(self):
        self.seed1_input.setText("12345")
        self.seed2_input.setText("67890")
        self.sample_size_input.setText("2000")
        self.num_bins_input.setText("16")
        self.alpha_input.setText("0.05")

    def show_results(self):
        if self.results_dialog:
            self.results_dialog.show()
            self.results_dialog.raise_()
            self.results_dialog.activateWindow()

    def generate_and_analyze(self):
        try:
            seed1 = int(self.seed1_input.text())
            seed2 = int(self.seed2_input.text())
            sample_size = int(self.sample_size_input.text())
            num_bins = int(self.num_bins_input.text())
            alpha = float(self.alpha_input.text())

            if sample_size <= 0 or num_bins <= 0:
                self._show_error("Объем выборки и число участков должны быть положительными.")
                return

            if not (0 < alpha < 1):
                self._show_error("Уровень значимости должен быть в интервале (0, 1).")
                return

            self.generate_btn.setEnabled(False)
            self.generate_btn.setText("Вычисление...")
            QApplication.processEvents()

            generator = MRG2Generator(seed1, seed2)
            sample = generator.generate_sample(sample_size)

            stats_results = StatisticsAnalyzer.calculate_statistics(sample)
            chi_square_results = StatisticsAnalyzer.chi_square_test(sample, num_bins, alpha, "uniform")

            self.plot_canvas.plot_uniform_data(sample, num_bins)

            html_content = self._format_results(
                stats_results, chi_square_results, sample_size, num_bins, alpha
            )

            if not self.results_dialog:
                self.results_dialog = ResultsDialog(self)

            self.results_dialog.set_results(html_content)
            self.results_dialog.show()

            self.results_btn.setEnabled(True)
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")

        except ValueError:
            self._show_error("Проверьте правильность введенных данных.")
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")
        except Exception as e:
            self._show_error(f"Произошла ошибка: {str(e)}")
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")

    def _format_results(self, stats, chi_square, sample_size, num_bins, alpha):
        confidence_level = 1 - alpha
        theoretical_mean = 0.5
        theoretical_variance = 1 / 12

        if chi_square["hypothesis_accepted"]:
            status_color = "#4CAF50"
            status_text = "ПРИНЯТА"
            conclusion = f"Выборка подчиняется равномерному распределению U(0,1) с доверительной вероятностью {confidence_level:.2f}."
        else:
            status_color = "#F44336"
            status_text = "ОТВЕРГНУТА"
            conclusion = f"Выборка НЕ подчиняется равномерному распределению U(0,1) с доверительной вероятностью {confidence_level:.2f}."

        html = f"""
        <style>
            body {{ 
                font-family: 'Segoe UI', Arial, sans-serif; 
                line-height: 1.8;
                padding: 0;
                margin: 0;
            }}
            .header {{ 
                color: #2196F3;
                font-weight: 700;
                font-size: 16px;
                margin-bottom: 10px;
                margin-top: 20px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .header:first-child {{
                margin-top: 0;
            }}
            .metric {{ 
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #E0E0E0;
            }}
            .metric:last-of-type {{
                border-bottom: 2px solid #E0E0E0;
            }}
            .metric-label {{ 
                color: #666;
                font-weight: 500;
            }}
            .metric-value {{ 
                color: #212121;
                font-weight: 700;
                font-family: 'Consolas', monospace;
            }}
            .metric-value.deviation {{ color: #FF9800; }}
            .metric-value.highlight {{ color: #2196F3; }}
            .conclusion {{ 
                background: {status_color};
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                font-size: 15px;
                font-weight: 600;
                margin-top: 25px;
            }}
            .conclusion-status {{
                font-size: 18px;
                margin-bottom: 8px;
                letter-spacing: 1px;
            }}
            .conclusion-text {{
                font-size: 13px;
                font-weight: 400;
                opacity: 0.95;
            }}
        </style>
        
        <div class="header">ПАРАМЕТРЫ ЭКСПЕРИМЕНТА</div>
        <div class="metric">
            <span class="metric-label">Объем выборки</span>
            <span class="metric-value highlight">{sample_size}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Число интервалов</span>
            <span class="metric-value highlight">{num_bins}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Доверительная вероятность</span>
            <span class="metric-value highlight">{confidence_level:.3f}</span>
        </div>
        
        <div class="header">МАТЕМАТИЧЕСКОЕ ОЖИДАНИЕ</div>
        <div class="metric">
            <span class="metric-label">Выборочное</span>
            <span class="metric-value">{stats['mean']:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Теоретическое</span>
            <span class="metric-value">{theoretical_mean:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Абсолютное отклонение</span>
            <span class="metric-value deviation">{abs(stats['mean'] - theoretical_mean):.6f}</span>
        </div>
        
        <div class="header">ДИСПЕРСИЯ</div>
        <div class="metric">
            <span class="metric-label">Выборочная</span>
            <span class="metric-value">{stats['variance']:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Теоретическая</span>
            <span class="metric-value">{theoretical_variance:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Абсолютное отклонение</span>
            <span class="metric-value deviation">{abs(stats['variance'] - theoretical_variance):.6f}</span>
        </div>
        
        <div class="header">КРИТЕРИЙ χ² ПИРСОНА</div>
        <div class="metric">
            <span class="metric-label">Наблюдаемое χ²</span>
            <span class="metric-value">{chi_square['chi_square']:.4f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Критическое χ²</span>
            <span class="metric-value">{chi_square['critical_value']:.4f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Степени свободы</span>
            <span class="metric-value">{chi_square['degrees_of_freedom']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">P-значение</span>
            <span class="metric-value">{chi_square['p_value']:.6f}</span>
        </div>
        
        <div class="conclusion">
            <div class="conclusion-status">ГИПОТЕЗА {status_text}</div>
            <div class="conclusion-text">{conclusion}</div>
        </div>
        """
        return html

    def _show_error(self, message):
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.warning(self, "Ошибка", message)


class CustomDistributionTab(QWidget):
    """Вкладка для генератора с заданным распределением"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_dialog = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        description = QLabel(
            "<b>Функция распределения F(x):</b><br>"
            "• F(x) = √x, x ∈ [0; 0.25)<br>"
            "• F(x) = 0.25x + 0.4375, x ∈ [0.25; 2.25]"
        )
        description.setStyleSheet(
            """
            QLabel {
                background-color: #E8F5E9;
                padding: 15px;
                border-radius: 8px;
                font-size: 12px;
                color: #2E7D32;
            }
        """
        )
        left_layout.addWidget(description)

        params_group = self._create_params_group()
        left_layout.addWidget(params_group)

        self.generate_btn = ModernButton("Сгенерировать", primary=True)
        self.generate_btn.clicked.connect(self.generate_and_analyze)
        left_layout.addWidget(self.generate_btn)

        self.results_btn = ModernButton("Показать результаты", primary=False)
        self.results_btn.clicked.connect(self.show_results)
        self.results_btn.setEnabled(False)
        left_layout.addWidget(self.results_btn)

        self.reset_btn = ModernButton("Сброс", primary=False)
        self.reset_btn.clicked.connect(self.reset_parameters)
        left_layout.addWidget(self.reset_btn)

        left_layout.addStretch()

        self.plot_canvas = PlotCanvas(self)

        layout.addWidget(left_widget, 1)
        layout.addWidget(self.plot_canvas, 2)

    def _create_params_group(self):
        group = ModernGroupBox("Параметры")
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        label_style = """
            QLabel {
                font-size: 13px;
                color: #616161;
                font-weight: 500;
            }
        """

        label1 = QLabel("Начальное значение y₁(0):")
        label1.setStyleSheet(label_style)
        layout.addWidget(label1, 0, 0)
        self.seed1_input = ModernLineEdit("12345")
        layout.addWidget(self.seed1_input, 0, 1)

        label2 = QLabel("Начальное значение y₂(0):")
        label2.setStyleSheet(label_style)
        layout.addWidget(label2, 1, 0)
        self.seed2_input = ModernLineEdit("67890")
        layout.addWidget(self.seed2_input, 1, 1)

        label3 = QLabel("Объем выборки:")
        label3.setStyleSheet(label_style)
        layout.addWidget(label3, 2, 0)
        self.sample_size_input = ModernLineEdit("1000")
        layout.addWidget(self.sample_size_input, 2, 1)

        label4 = QLabel("Число участков (15 или 25):")
        label4.setStyleSheet(label_style)
        layout.addWidget(label4, 3, 0)
        self.num_bins_input = ModernLineEdit("15")
        layout.addWidget(self.num_bins_input, 3, 1)

        label5 = QLabel("Критерий проверки:")
        label5.setStyleSheet(label_style)
        layout.addWidget(label5, 4, 0)

        self.test_combo = ModernComboBox()
        self.test_combo.addItem("χ² Пирсона", "chi2")
        self.test_combo.addItem("Колмогорова", "kolmogorov")
        layout.addWidget(self.test_combo, 4, 1)

        group.setLayout(layout)
        return group

    def reset_parameters(self):
        self.seed1_input.setText("12345")
        self.seed2_input.setText("67890")
        self.sample_size_input.setText("1000")
        self.num_bins_input.setText("15")
        self.test_combo.setCurrentIndex(0)

    def show_results(self):
        if self.results_dialog:
            self.results_dialog.show()
            self.results_dialog.raise_()
            self.results_dialog.activateWindow()

    def generate_and_analyze(self):
        try:
            seed1 = int(self.seed1_input.text())
            seed2 = int(self.seed2_input.text())
            sample_size = int(self.sample_size_input.text())
            num_bins = int(self.num_bins_input.text())
            test_type = self.test_combo.currentData()

            if sample_size < 1000:
                self._show_error("Объем выборки должен быть не менее 1000.")
                return

            if num_bins not in [15, 25]:
                self._show_error("Число участков должно быть 15 или 25.")
                return

            self.generate_btn.setEnabled(False)
            self.generate_btn.setText("Вычисление...")
            QApplication.processEvents()

            rng = MRG2Generator(seed1, seed2)
            custom_gen = CustomDistributionGenerator(rng)
            sample = custom_gen.generate_sample(sample_size)

            stats_results = StatisticsAnalyzer.calculate_statistics(sample)

            if test_type == "chi2":
                test_results = StatisticsAnalyzer.chi_square_test(
                    sample, num_bins, 0.05, "custom", CustomDistributionGenerator.cdf
                )
                test_name = "χ² Пирсона"
            else:
                test_results = StatisticsAnalyzer.kolmogorov_test(
                    sample, CustomDistributionGenerator.cdf, 0.05
                )
                test_name = "Колмогорова"

            self.plot_canvas.plot_custom_data(sample, num_bins)

            html_content = self._format_results(stats_results, test_results, sample_size, num_bins, test_name)

            if not self.results_dialog:
                self.results_dialog = ResultsDialog(self)

            self.results_dialog.set_results(html_content)
            self.results_dialog.show()

            self.results_btn.setEnabled(True)
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")

        except ValueError as e:
            self._show_error(f"Ошибка ввода данных: {str(e)}")
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")
        except Exception as e:
            self._show_error(f"Произошла ошибка: {str(e)}")
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")

    def _format_results(self, stats, test_results, sample_size, num_bins, test_name):
        theoretical_mean = CustomDistributionGenerator.theoretical_mean()
        theoretical_variance = CustomDistributionGenerator.theoretical_variance()

        if "hypothesis_accepted" in test_results and test_results["hypothesis_accepted"]:
            status_color = "#4CAF50"
            status_text = "ПРИНЯТА"
            conclusion = f"Выборка подчиняется заданному распределению с доверительной вероятностью 0.95 (критерий {test_name})."
        else:
            status_color = "#F44336"
            status_text = "ОТВЕРГНУТА"
            conclusion = f"Выборка НЕ подчиняется заданному распределению с доверительной вероятностью 0.95 (критерий {test_name})."

        if test_name == "χ² Пирсона":
            test_block = f"""
            <div class="header">КРИТЕРИЙ χ² ПИРСОНА</div>
            <div class="metric">
                <span class="metric-label">Наблюдаемое χ²</span>
                <span class="metric-value">{test_results['chi_square']:.4f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Критическое χ²</span>
                <span class="metric-value">{test_results['critical_value']:.4f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Степени свободы</span>
                <span class="metric-value">{test_results['degrees_of_freedom']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">P-значение</span>
                <span class="metric-value">{test_results['p_value']:.6f}</span>
            </div>
            """
        else:
            test_block = f"""
            <div class="header">КРИТЕРИЙ КОЛМОГОРОВА</div>
            <div class="metric">
                <span class="metric-label">Статистика D</span>
                <span class="metric-value">{test_results['d_statistic']:.6f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Критическое значение</span>
                <span class="metric-value">{test_results['critical_value']:.6f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">D+ (сверху)</span>
                <span class="metric-value">{test_results['d_plus']:.6f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">D- (снизу)</span>
                <span class="metric-value">{test_results['d_minus']:.6f}</span>
            </div>
            """

        html = f"""
        <style>
            body {{ 
                font-family: 'Segoe UI', Arial, sans-serif; 
                line-height: 1.8;
                padding: 0;
                margin: 0;
            }}
            .header {{ 
                color: #4CAF50;
                font-weight: 700;
                font-size: 16px;
                margin-bottom: 10px;
                margin-top: 20px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .header:first-child {{
                margin-top: 0;
            }}
            .metric {{ 
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #E0E0E0;
            }}
            .metric:last-of-type {{
                border-bottom: 2px solid #E0E0E0;
            }}
            .metric-label {{ 
                color: #666;
                font-weight: 500;
            }}
            .metric-value {{ 
                color: #212121;
                font-weight: 700;
                font-family: 'Consolas', monospace;
            }}
            .metric-value.deviation {{ color: #FF9800; }}
            .metric-value.highlight {{ color: #4CAF50; }}
            .conclusion {{ 
                background: {status_color};
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                font-size: 15px;
                font-weight: 600;
                margin-top: 25px;
            }}
            .conclusion-status {{
                font-size: 18px;
                margin-bottom: 8px;
                letter-spacing: 1px;
            }}
            .conclusion-text {{
                font-size: 13px;
                font-weight: 400;
                opacity: 0.95;
            }}
        </style>
        
        <div class="header">ПАРАМЕТРЫ ЭКСПЕРИМЕНТА</div>
        <div class="metric">
            <span class="metric-label">Объем выборки</span>
            <span class="metric-value highlight">{sample_size}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Число интервалов</span>
            <span class="metric-value highlight">{num_bins}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Используемый критерий</span>
            <span class="metric-value highlight">{test_name}</span>
        </div>
        
        <div class="header">МАТЕМАТИЧЕСКОЕ ОЖИДАНИЕ</div>
        <div class="metric">
            <span class="metric-label">Выборочное</span>
            <span class="metric-value">{stats['mean']:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Теоретическое</span>
            <span class="metric-value">{theoretical_mean:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Абсолютное отклонение</span>
            <span class="metric-value deviation">{abs(stats['mean'] - theoretical_mean):.6f}</span>
        </div>
        
        <div class="header">ДИСПЕРСИЯ</div>
        <div class="metric">
            <span class="metric-label">Выборочная</span>
            <span class="metric-value">{stats['variance']:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Теоретическая</span>
            <span class="metric-value">{theoretical_variance:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Абсолютное отклонение</span>
            <span class="metric-value deviation">{abs(stats['variance'] - theoretical_variance):.6f}</span>
        </div>
        
        {test_block}
        
        <div class="conclusion">
            <div class="conclusion-status">ГИПОТЕЗА {status_text}</div>
            <div class="conclusion-text">{conclusion}</div>
        </div>
        """
        return html

    def _show_error(self, message):
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.warning(self, "Ошибка", message)


class NormalDistributionTab(QWidget):
    """Вкладка для генератора с нормальным распределением"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_dialog = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        description = QLabel(
            "<b>Нормальное распределение:</b><br>"
            "N(μ, σ²) - распределение Гаусса<br>"
            "По умолчанию: N(1, 0.7)"
        )
        description.setStyleSheet(
            """
            QLabel {
                background-color: #F3E5F5;
                padding: 15px;
                border-radius: 8px;
                font-size: 12px;
                color: #6A1B9A;
            }
        """
        )
        left_layout.addWidget(description)

        params_group = self._create_params_group()
        left_layout.addWidget(params_group)

        self.generate_btn = ModernButton("Сгенерировать", primary=True)
        self.generate_btn.clicked.connect(self.generate_and_analyze)
        left_layout.addWidget(self.generate_btn)

        self.results_btn = ModernButton("Показать результаты", primary=False)
        self.results_btn.clicked.connect(self.show_results)
        self.results_btn.setEnabled(False)
        left_layout.addWidget(self.results_btn)

        self.reset_btn = ModernButton("Сброс", primary=False)
        self.reset_btn.clicked.connect(self.reset_parameters)
        left_layout.addWidget(self.reset_btn)

        left_layout.addStretch()

        self.plot_canvas = PlotCanvas(self)

        layout.addWidget(left_widget, 1)
        layout.addWidget(self.plot_canvas, 2)

    def _create_params_group(self):
        group = ModernGroupBox("Параметры")
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        label_style = """
            QLabel {
                font-size: 13px;
                color: #616161;
                font-weight: 500;
            }
        """

        label1 = QLabel("Начальное значение y₁(0):")
        label1.setStyleSheet(label_style)
        layout.addWidget(label1, 0, 0)
        self.seed1_input = ModernLineEdit("12345")
        layout.addWidget(self.seed1_input, 0, 1)

        label2 = QLabel("Начальное значение y₂(0):")
        label2.setStyleSheet(label_style)
        layout.addWidget(label2, 1, 0)
        self.seed2_input = ModernLineEdit("67890")
        layout.addWidget(self.seed2_input, 1, 1)

        label3 = QLabel("Мат. ожидание μ:")
        label3.setStyleSheet(label_style)
        layout.addWidget(label3, 2, 0)
        self.mu_input = ModernLineEdit("1.0")
        layout.addWidget(self.mu_input, 2, 1)

        label4 = QLabel("Дисперсия σ²:")
        label4.setStyleSheet(label_style)
        layout.addWidget(label4, 3, 0)
        self.sigma_squared_input = ModernLineEdit("0.7")
        layout.addWidget(self.sigma_squared_input, 3, 1)

        label5 = QLabel("Объем выборки:")
        label5.setStyleSheet(label_style)
        layout.addWidget(label5, 4, 0)
        self.sample_size_input = ModernLineEdit("1000")
        layout.addWidget(self.sample_size_input, 4, 1)

        label6 = QLabel("Число участков (15 или 25):")
        label6.setStyleSheet(label_style)
        layout.addWidget(label6, 5, 0)
        self.num_bins_input = ModernLineEdit("15")
        layout.addWidget(self.num_bins_input, 5, 1)

        label7 = QLabel("Критерий проверки:")
        label7.setStyleSheet(label_style)
        layout.addWidget(label7, 6, 0)

        self.test_combo = ModernComboBox()
        self.test_combo.addItem("χ² Пирсона", "chi2")
        self.test_combo.addItem("Колмогорова", "kolmogorov")
        layout.addWidget(self.test_combo, 6, 1)

        group.setLayout(layout)
        return group

    def reset_parameters(self):
        self.seed1_input.setText("12345")
        self.seed2_input.setText("67890")
        self.mu_input.setText("1.0")
        self.sigma_squared_input.setText("0.7")
        self.sample_size_input.setText("1000")
        self.num_bins_input.setText("15")
        self.test_combo.setCurrentIndex(0)

    def show_results(self):
        if self.results_dialog:
            self.results_dialog.show()
            self.results_dialog.raise_()
            self.results_dialog.activateWindow()

    def generate_and_analyze(self):
        try:
            seed1 = int(self.seed1_input.text())
            seed2 = int(self.seed2_input.text())
            mu = float(self.mu_input.text())
            sigma_squared = float(self.sigma_squared_input.text())
            sample_size = int(self.sample_size_input.text())
            num_bins = int(self.num_bins_input.text())
            test_type = self.test_combo.currentData()

            if sample_size < 1000:
                self._show_error("Объем выборки должен быть не менее 1000.")
                return

            if num_bins not in [15, 25]:
                self._show_error("Число участков должно быть 15 или 25.")
                return

            if sigma_squared <= 0:
                self._show_error("Дисперсия должна быть положительной.")
                return

            self.generate_btn.setEnabled(False)
            self.generate_btn.setText("Вычисление...")
            QApplication.processEvents()

            rng = MRG2Generator(seed1, seed2)
            normal_gen = NormalDistributionGenerator(rng, mu, sigma_squared)
            sample = normal_gen.generate_sample(sample_size)

            stats_results = StatisticsAnalyzer.calculate_statistics(sample)

            if test_type == "chi2":
                test_results = StatisticsAnalyzer.chi_square_test(
                    sample, num_bins, 0.05, "normal", mu=mu, sigma_squared=sigma_squared
                )
                test_name = "χ² Пирсона"
            else:

                def norm_cdf(x):
                    return stats.norm.cdf(x, mu, np.sqrt(sigma_squared))

                test_results = StatisticsAnalyzer.kolmogorov_test(sample, norm_cdf, 0.05)
                test_name = "Колмогорова"

            self.plot_canvas.plot_normal_data(sample, mu, sigma_squared, num_bins)

            html_content = self._format_results(
                stats_results, test_results, sample_size, num_bins, test_name, mu, sigma_squared
            )

            if not self.results_dialog:
                self.results_dialog = ResultsDialog(self)

            self.results_dialog.set_results(html_content)
            self.results_dialog.show()

            self.results_btn.setEnabled(True)
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")

        except ValueError as e:
            self._show_error(f"Ошибка ввода данных: {str(e)}")
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")
        except Exception as e:
            self._show_error(f"Произошла ошибка: {str(e)}")
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")

    def _format_results(self, stats, test_results, sample_size, num_bins, test_name, mu, sigma_squared):
        theoretical_mean = mu
        theoretical_variance = sigma_squared

        if "hypothesis_accepted" in test_results and test_results["hypothesis_accepted"]:
            status_color = "#4CAF50"
            status_text = "ПРИНЯТА"
            conclusion = f"Выборка подчиняется нормальному распределению N({mu}, {sigma_squared}) с доверительной вероятностью 0.95 (критерий {test_name})."
        else:
            status_color = "#F44336"
            status_text = "ОТВЕРГНУТА"
            conclusion = f"Выборка НЕ подчиняется нормальному распределению N({mu}, {sigma_squared}) с доверительной вероятностью 0.95 (критерий {test_name})."

        if test_name == "χ² Пирсона":
            test_block = f"""
            <div class="header">КРИТЕРИЙ χ² ПИРСОНА</div>
            <div class="metric">
                <span class="metric-label">Наблюдаемое χ²</span>
                <span class="metric-value">{test_results['chi_square']:.4f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Критическое χ²</span>
                <span class="metric-value">{test_results['critical_value']:.4f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Степени свободы</span>
                <span class="metric-value">{test_results['degrees_of_freedom']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">P-значение</span>
                <span class="metric-value">{test_results['p_value']:.6f}</span>
            </div>
            """
        else:
            test_block = f"""
            <div class="header">КРИТЕРИЙ КОЛМОГОРОВА</div>
            <div class="metric">
                <span class="metric-label">Статистика D</span>
                <span class="metric-value">{test_results['d_statistic']:.6f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Критическое значение</span>
                <span class="metric-value">{test_results['critical_value']:.6f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">D+ (сверху)</span>
                <span class="metric-value">{test_results['d_plus']:.6f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">D- (снизу)</span>
                <span class="metric-value">{test_results['d_minus']:.6f}</span>
            </div>
            """

        html = f"""
        <style>
            body {{ 
                font-family: 'Segoe UI', Arial, sans-serif; 
                line-height: 1.8;
                padding: 0;
                margin: 0;
            }}
            .header {{ 
                color: #9C27B0;
                font-weight: 700;
                font-size: 16px;
                margin-bottom: 10px;
                margin-top: 20px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .header:first-child {{
                margin-top: 0;
            }}
            .metric {{ 
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #E0E0E0;
            }}
            .metric:last-of-type {{
                border-bottom: 2px solid #E0E0E0;
            }}
            .metric-label {{ 
                color: #666;
                font-weight: 500;
            }}
            .metric-value {{ 
                color: #212121;
                font-weight: 700;
                font-family: 'Consolas', monospace;
            }}
            .metric-value.deviation {{ color: #FF9800; }}
            .metric-value.highlight {{ color: #9C27B0; }}
            .conclusion {{ 
                background: {status_color};
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                font-size: 15px;
                font-weight: 600;
                margin-top: 25px;
            }}
            .conclusion-status {{
                font-size: 18px;
                margin-bottom: 8px;
                letter-spacing: 1px;
            }}
            .conclusion-text {{
                font-size: 13px;
                font-weight: 400;
                opacity: 0.95;
            }}
        </style>
        
        <div class="header">ПАРАМЕТРЫ ЭКСПЕРИМЕНТА</div>
        <div class="metric">
            <span class="metric-label">Объем выборки</span>
            <span class="metric-value highlight">{sample_size}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Число интервалов</span>
            <span class="metric-value highlight">{num_bins}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Используемый критерий</span>
            <span class="metric-value highlight">{test_name}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Распределение</span>
            <span class="metric-value highlight">N({mu}, {sigma_squared})</span>
        </div>
        
        <div class="header">МАТЕМАТИЧЕСКОЕ ОЖИДАНИЕ</div>
        <div class="metric">
            <span class="metric-label">Выборочное</span>
            <span class="metric-value">{stats['mean']:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Теоретическое (μ)</span>
            <span class="metric-value">{theoretical_mean:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Абсолютное отклонение</span>
            <span class="metric-value deviation">{abs(stats['mean'] - theoretical_mean):.6f}</span>
        </div>
        
        <div class="header">ДИСПЕРСИЯ</div>
        <div class="metric">
            <span class="metric-label">Выборочная</span>
            <span class="metric-value">{stats['variance']:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Теоретическая (σ²)</span>
            <span class="metric-value">{theoretical_variance:.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Абсолютное отклонение</span>
            <span class="metric-value deviation">{abs(stats['variance'] - theoretical_variance):.6f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">СКО (σ)</span>
            <span class="metric-value">{np.sqrt(sigma_squared):.6f}</span>
        </div>
        
        {test_block}
        
        <div class="conclusion">
            <div class="conclusion-status">ГИПОТЕЗА {status_text}</div>
            <div class="conclusion-text">{conclusion}</div>
        </div>
        """
        return html

    def _show_error(self, message):
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.warning(self, "Ошибка", message)


class MainWindow(QMainWindow):
    """Главное окно приложения с современным дизайном"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор случайных чисел и величин")
        self.setGeometry(100, 50, 1400, 950)

        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #FFFFFF;")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header_widget = self._create_header()
        main_layout.addWidget(header_widget)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F5F5F5;
                color: #616161;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #2196F3;
                border-bottom: 3px solid #2196F3;
            }
            QTabBar::tab:hover {
                background-color: #E3F2FD;
            }
        """
        )

        self.uniform_tab = UniformGeneratorTab()
        self.custom_tab = CustomDistributionTab()
        self.normal_tab = NormalDistributionTab()

        self.tabs.addTab(self.uniform_tab, "Равномерное U(0,1)")
        self.tabs.addTab(self.custom_tab, "Заданное F(x)")
        self.tabs.addTab(self.normal_tab, "Нормальное N(μ, σ²)")

        main_layout.addWidget(self.tabs)

    def _create_header(self):
        header = QFrame()
        header.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #21CBF3);
                border-radius: 8px;
            }
        """
        )

        layout = QVBoxLayout(header)
        layout.setSpacing(3)
        layout.setContentsMargins(15, 12, 15, 12)

        title = QLabel("Генератор случайных чисел и величин")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: white;
                background: transparent;
            }
        """
        )

        subtitle = QLabel("Генераторы: Равномерное, Заданное и Нормальное распределения")
        subtitle.setStyleSheet(
            """
            QLabel {
                font-size: 11px;
                color: white;
                font-weight: 400;
                background: transparent;
            }
        """
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)

        return header


def main():
    """Главная функция приложения"""
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(33, 33, 33))
    palette.setColor(QPalette.ColorRole.Base, QColor(250, 250, 250))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.Text, QColor(33, 33, 33))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(33, 33, 33))
    app.setPalette(palette)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
