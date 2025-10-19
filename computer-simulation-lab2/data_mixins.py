import numpy as np
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox


class DataMixin:
    def create_matrices(self):
        """Создает пустые матрицы заданного размера"""
        positions = self.positions_spin.value()
        transitions = self.transitions_spin.value()

        self.f_table.setRowCount(positions)
        self.f_table.setColumnCount(transitions)
        self.f_table.setHorizontalHeaderLabels([f"T{i+1}" for i in range(transitions)])
        self.f_table.setVerticalHeaderLabels([f"P{i+1}" for i in range(positions)])

        self.h_table.setRowCount(transitions)
        self.h_table.setColumnCount(positions)
        self.h_table.setHorizontalHeaderLabels([f"P{i+1}" for i in range(positions)])
        self.h_table.setVerticalHeaderLabels([f"T{i+1}" for i in range(transitions)])

        self.m0_table.setRowCount(positions)
        self.m0_table.setColumnCount(1)
        self.m0_table.setHorizontalHeaderLabels(["M0"])
        self.m0_table.setVerticalHeaderLabels([f"P{i+1}" for i in range(positions)])

        for table in [self.f_table, self.h_table, self.m0_table]:
            for i in range(table.rowCount()):
                for j in range(table.columnCount()):
                    table.setItem(i, j, QTableWidgetItem("0"))

    def load_network(self):
        """Загружает выбранную сеть (исходную или модифицированную)"""
        self.positions_spin.setValue(6)
        self.transitions_spin.setValue(6)
        self.create_matrices()

        if self.original_radio.isChecked():
            f_data = [
                [1, 0, 0, 0, 0, 0],  # P1
                [0, 1, 0, 0, 0, 1],  # P2
                [0, 1, 0, 0, 0, 0],  # P3
                [0, 0, 1, 0, 1, 0],  # P4
                [0, 0, 0, 1, 0, 0],  # P5
                [0, 0, 0, 0, 1, 0],  # P6
            ]
            h_data = [
                [0, 1, 0, 0, 0, 0],  # T1 -> P2
                [0, 0, 1, 0, 0, 0],  # T2 -> P3
                [0, 0, 0, 1, 0, 0],  # T3 -> P4
                [0, 0, 0, 0, 1, 0],  # T4 -> P5
                [0, 0, 0, 0, 0, 1],  # T5 -> P6
                [1, 0, 0, 0, 0, 0],  # T6 -> P1
            ]
            m0_data = [1, 0, 0, 0, 0, 0]  # Одна метка в P1
        else:
            # Модифицированная сеть
            f_data = [
                [1, 0, 0, 0, 0, 0],  # P1 -> T1
                [0, 1, 0, 0, 0, 0],  # P2 -> T2
                [0, 0, 1, 0, 0, 0],  # P3 -> T3
                [0, 0, 0, 1, 0, 0],  # P4 -> T4
                [0, 0, 0, 0, 1, 0],  # P5 -> T5
                [0, 0, 0, 0, 0, 1],  # P6 -> T6
            ]
            h_data = [
                [0, 1, 0, 0, 0, 0],  # T1 -> P2
                [0, 0, 1, 0, 0, 0],  # T2 -> P3
                [0, 0, 0, 1, 0, 0],  # T3 -> P4
                [0, 0, 0, 0, 1, 0],  # T4 -> P5
                [0, 0, 0, 0, 0, 1],  # T5 -> P6
                [1, 0, 0, 0, 0, 0],  # T6 -> P1
            ]
            m0_data = [1, 0, 0, 0, 0, 0]  # Одна метка в P1

        for i in range(len(f_data)):
            for j in range(len(f_data[0])):
                self.f_table.setItem(i, j, QTableWidgetItem(str(f_data[i][j])))

        for i in range(len(h_data)):
            for j in range(len(h_data[0])):
                self.h_table.setItem(i, j, QTableWidgetItem(str(h_data[i][j])))

        for i in range(len(m0_data)):
            self.m0_table.setItem(i, 0, QTableWidgetItem(str(m0_data[i])))

    def get_matrices_from_tables(self):
        """Извлекает матрицы из таблиц"""
        try:
            rows_f = self.f_table.rowCount()
            cols_f = self.f_table.columnCount()
            self.F = np.zeros((rows_f, cols_f), dtype=int)

            for i in range(rows_f):
                for j in range(cols_f):
                    item = self.f_table.item(i, j)
                    if item:
                        self.F[i][j] = int(item.text())

            rows_h = self.h_table.rowCount()
            cols_h = self.h_table.columnCount()
            self.H = np.zeros((rows_h, cols_h), dtype=int)

            for i in range(rows_h):
                for j in range(cols_h):
                    item = self.h_table.item(i, j)
                    if item:
                        self.H[i][j] = int(item.text())

            rows_m = self.m0_table.rowCount()
            self.M0 = np.zeros(rows_m, dtype=int)

            for i in range(rows_m):
                item = self.m0_table.item(i, 0)
                if item:
                    self.M0[i] = int(item.text())

            self.C = self.H.T - self.F

            return True

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при чтении матриц: {str(e)}")
            return False
