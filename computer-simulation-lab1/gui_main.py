import math
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QHBoxLayout,
    QLabel,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from analysis import RegressionAnalysis
from plot_widget import PlotWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.analysis = RegressionAnalysis()
        self.analysis.calculate_basic_stats()
        self.models = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Лабораторная работа №1 - Компьютерное моделирование")
        self.setGeometry(100, 100, 1300, 850)

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f7f9fc;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 6px;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #aaa;
                border-bottom-color: #ccc;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #fdfdfd;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                font-family: Consolas, monospace;
                font-size: 11pt;
            }
            QTableWidget {
                background: #ffffff;
                gridline-color: #ccc;
                font-size: 11pt;
            }
        """
        )

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.plot_tab, self.report_tab = QWidget(), QWidget()
        self.tabs.addTab(self.plot_tab, "📊 Графики")
        self.tabs.addTab(self.report_tab, "📑 Отчёт")

        self.init_plot_tab()
        self.init_report_tab()

    def init_plot_tab(self):
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Выполнить анализ")
        self.analyze_btn.clicked.connect(self.perform_analysis)
        btn_layout.addWidget(self.analyze_btn, alignment=Qt.AlignLeft)

        layout.addLayout(btn_layout)

        self.plot_widget = PlotWidget()
        layout.addWidget(self.plot_widget)
        self.plot_tab.setLayout(layout)

    def init_report_tab(self):
        layout = QVBoxLayout()

        intro_label = QLabel("<h2>Корреляционный анализ</h2>")
        layout.addWidget(intro_label)

        self.report_intro = QTextEdit()
        self.report_intro.setReadOnly(True)
        layout.addWidget(self.report_intro)

        table_label = QLabel("<h2>Регрессионный анализ</h2>")
        layout.addWidget(table_label)

        self.report_table = QTableWidget()
        layout.addWidget(self.report_table)

        summary_label = QLabel("<h2>Выводы</h2>")
        layout.addWidget(summary_label)

        self.report_summary = QTextEdit()
        self.report_summary.setReadOnly(True)
        layout.addWidget(self.report_summary)

        self.report_tab.setLayout(layout)

    def perform_analysis(self):
        r = self.analysis.correlation_coefficient()
        is_sig, t_calc = self.analysis.correlation_significance(r)

        self.models.clear()

        a, b = self.analysis.linear_regression()
        y = [a + b * x for x in self.analysis.x]
        rmse, mare, r2, _, _ = self.analysis.calculate_errors(y)
        sig, F = self.analysis.model_significance(r2, 2)
        self.models["Линейная"] = dict(
            eq=f"y = {a:.4f} + {b:.4f}x",
            func=lambda xx, a=a, b=b: a + b * xx,
            rmse=rmse,
            mare=mare,
            r2=r2,
            F=F,
            sig=sig,
        )

        a, b, c = self.analysis.quadratic_regression()
        y = [a + b * x + c * x**2 for x in self.analysis.x]
        rmse, mare, r2, _, _ = self.analysis.calculate_errors(y)
        sig, F = self.analysis.model_significance(r2, 3)
        self.models["Квадратичная"] = dict(
            eq=f"y = {a:.4f} + {b:.4f}x + {c:.4f}x²",
            func=lambda xx, a=a, b=b, c=c: a + b * xx + c * xx**2,
            rmse=rmse,
            mare=mare,
            r2=r2,
            F=F,
            sig=sig,
        )

        a, b, c, d = self.analysis.cubic_regression()
        y = [a + b * x + c * x**2 + d * x**3 for x in self.analysis.x]
        rmse, mare, r2, _, _ = self.analysis.calculate_errors(y)
        sig, F = self.analysis.model_significance(r2, 4)
        self.models["Кубическая"] = dict(
            eq=f"y = {a:.4f} + {b:.4f}x + {c:.4f}x² + {d:.4f}x³",
            func=lambda xx, a=a, b=b, c=c, d=d: a + b * xx + c * xx**2 + d * xx**3,
            rmse=rmse,
            mare=mare,
            r2=r2,
            F=F,
            sig=sig,
        )

        a, b = self.analysis.exponential_regression()
        y = [a * math.exp(b * x) for x in self.analysis.x]
        rmse, mare, r2, _, _ = self.analysis.calculate_errors(y)
        sig, F = self.analysis.model_significance(r2, 2)
        self.models["Экспоненциальная"] = dict(
            eq=f"y = {a:.4f} * exp({b:.4f}x)",
            func=lambda xx, a=a, b=b: a * math.exp(b * xx),
            rmse=rmse,
            mare=mare,
            r2=r2,
            F=F,
            sig=sig,
        )

        a, b = self.analysis.power_regression()
        y = [a * (x**b) if x > 0 else 0 for x in self.analysis.x]
        rmse, mare, r2, _, _ = self.analysis.calculate_errors(y)
        sig, F = self.analysis.model_significance(r2, 2)
        self.models["Степенная"] = dict(
            eq=f"y = {a:.4f} * x^{b:.4f}",
            func=lambda xx, a=a, b=b: a * (xx**b) if xx > 0 else 0,
            rmse=rmse,
            mare=mare,
            r2=r2,
            F=F,
            sig=sig,
        )

        intro_text = []
        intro_text.append(f"Коэффициент корреляции r = {r:.4f}")
        intro_text.append(f"t-статистика = {t_calc:.4f}")
        intro_text.append(f"Значимость: {'Да' if is_sig else 'Нет'}")

        if abs(r) < 0.3:
            interp = "слабая"
        elif abs(r) < 0.7:
            interp = "умеренная"
        else:
            interp = "сильная"
        direction = "положительная" if r > 0 else "отрицательная"
        intro_text.append(f"Вывод: связь {interp} {direction}")

        self.report_intro.setText("\n".join(intro_text))

        self.report_table.setRowCount(len(self.models))
        self.report_table.setColumnCount(7)
        self.report_table.setHorizontalHeaderLabels(
            [
                "Модель",
                "Уравнение",
                "СКО",
                "Относительная ошибка (%)",
                "Коэф. детерминации (R²)",
                "F-критерий Фишера",
                "Значимость",
            ]
        )

        best_rmse = min(self.models.items(), key=lambda kv: kv[1]["rmse"])
        best_r2 = max(self.models.items(), key=lambda kv: kv[1]["r2"])

        for i, (name, m) in enumerate(self.models.items()):
            items = [
                QTableWidgetItem(name),
                QTableWidgetItem(m["eq"]),
                QTableWidgetItem(f"{m['rmse']:.4f}"),
                QTableWidgetItem(f"{m['mare']:.2f}"),
                QTableWidgetItem(f"{m['r2']:.4f}"),
                QTableWidgetItem(f"{m['F']:.2f}"),
                QTableWidgetItem("Да" if m["sig"] else "Нет"),
            ]

            if name == best_rmse[0] and name == best_r2[0]:
                bg_color = Qt.yellow
            elif name == best_rmse[0]:
                bg_color = Qt.green
            elif name == best_r2[0]:
                bg_color = Qt.cyan
            else:
                bg_color = None

            for j, item in enumerate(items):
                if j == 0:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)

                if j == 6:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                    if m["sig"]:
                        item.setForeground(QColor("darkgreen"))
                    else:
                        item.setForeground(QColor("red"))

                if bg_color:
                    item.setBackground(bg_color)

                self.report_table.setItem(i, j, item)

        self.report_table.resizeColumnsToContents()
        self.report_table.horizontalHeader().setStretchLastSection(True)

        summary = []
        summary.append(
            f"Лучшая модель по среднеквадратичной ошибке: {best_rmse[0]} ({best_rmse[1]['eq']})"
        )
        summary.append(
            f"Лучшая модель по коэффициенту детерминации R²: {best_r2[0]} ({best_r2[1]['eq']})"
        )
        summary.append(f"Рекомендуемая модель: {best_rmse[0]}")

        self.report_summary.setText("\n".join(summary))

        self.plot_results()

    def plot_results(self):
        self.plot_widget.figure.clear()
        for i, (name, m) in enumerate(self.models.items()):
            ax = self.plot_widget.figure.add_subplot(2, 3, i + 1)
            ax.scatter(
                self.analysis.x,
                self.analysis.y,
                color="red",
                s=50,
                label="Данные",
                zorder=3,
            )
            ax.axhline(
                self.analysis.y_mean,
                color="blue",
                linestyle="--",
                alpha=0.5,
                label=f"Среднее Y",
            )
            ax.axvline(
                self.analysis.x_mean,
                color="green",
                linestyle="--",
                alpha=0.5,
                label=f"Среднее X",
            )
            x_new = [
                min(self.analysis.x)
                + j * (max(self.analysis.x) - min(self.analysis.x)) / 200
                for j in range(201)
            ]
            y_new = [m["func"](xx) for xx in x_new]
            ax.plot(x_new, y_new, label=f"Модель: {name}", color="black")
            ax.set_title(name)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc="best")
        self.plot_widget.figure.tight_layout()
        self.plot_widget.canvas.draw()
