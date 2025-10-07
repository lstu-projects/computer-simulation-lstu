# data_mixins.py

import numpy as np
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QFileDialog

class DataMixin:
    def create_matrices(self):
        """Создает пустые матрицы заданного размера"""
        positions = self.positions_spin.value()
        transitions = self.transitions_spin.value()
        
        # Матрица F (P×T)
        self.f_table.setRowCount(positions)
        self.f_table.setColumnCount(transitions)
        self.f_table.setHorizontalHeaderLabels([f"T{i+1}" for i in range(transitions)])
        self.f_table.setVerticalHeaderLabels([f"P{i+1}" for i in range(positions)])
        
        # Матрица H (T×P)
        self.h_table.setRowCount(transitions)
        self.h_table.setColumnCount(positions)
        self.h_table.setHorizontalHeaderLabels([f"P{i+1}" for i in range(positions)])
        self.h_table.setVerticalHeaderLabels([f"T{i+1}" for i in range(transitions)])
        
        # Начальная разметка M0 (P×1)
        self.m0_table.setRowCount(positions)
        self.m0_table.setColumnCount(1)
        self.m0_table.setHorizontalHeaderLabels(["M0"])
        self.m0_table.setVerticalHeaderLabels([f"P{i+1}" for i in range(positions)])
        
        # Заполняем нулями
        for table in [self.f_table, self.h_table, self.m0_table]:
            for i in range(table.rowCount()):
                for j in range(table.columnCount()):
                    table.setItem(i, j, QTableWidgetItem("0"))
    
    def load_example(self):
        """Загружает пример из варианта 2, модифицированный для живости"""
        # Устанавливаем размер
        self.positions_spin.setValue(6)
        self.transitions_spin.setValue(6)
        self.create_matrices()
        
        # Матрица F (входы) - цикл для живости
        f_data = [
            [1, 0, 0, 0, 0, 0],  # P1 -> T1
            [0, 1, 0, 0, 0, 0],  # P2 -> T2
            [0, 0, 1, 0, 0, 0],  # P3 -> T3
            [0, 0, 0, 1, 0, 0],  # P4 -> T4
            [0, 0, 0, 0, 1, 0],  # P5 -> T5
            [0, 0, 0, 0, 0, 1],  # P6 -> T6
        ]
        
        # Матрица H (выходы)
        h_data = [
            [0, 1, 0, 0, 0, 0],  # T1 -> P2
            [0, 0, 1, 0, 0, 0],  # T2 -> P3
            [0, 0, 0, 1, 0, 0],  # T3 -> P4
            [0, 0, 0, 0, 1, 0],  # T4 -> P5
            [0, 0, 0, 0, 0, 1],  # T5 -> P6
            [1, 0, 0, 0, 0, 0],  # T6 -> P1
        ]
        
        # Начальная разметка
        m0_data = [1, 0, 0, 0, 0, 0]  # Одна метка в P1
        
        # Заполняем таблицы
        for i in range(len(f_data)):
            for j in range(len(f_data[0])):
                self.f_table.setItem(i, j, QTableWidgetItem(str(f_data[i][j])))
        
        for i in range(len(h_data)):
            for j in range(len(h_data[0])):
                self.h_table.setItem(i, j, QTableWidgetItem(str(h_data[i][j])))
        
        for i in range(len(m0_data)):
            self.m0_table.setItem(i, 0, QTableWidgetItem(str(m0_data[i])))
    
    def load_from_file(self):
        """Загружает матрицы из файла"""
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "Text files (*.txt)")
            if not filename:
                return
            
            with open(filename, 'r') as f:
                lines = f.readlines()
                lines = [l.strip() for l in lines if l.strip()]
            
            idx = 0
            # Количество позиций и переходов
            p, t = map(int, lines[idx].split())
            idx += 1
            
            self.positions_spin.setValue(p)
            self.transitions_spin.setValue(t)
            self.create_matrices()
            
            # Матрица F (p строк, t столбцов)
            for i in range(p):
                row = list(map(int, lines[idx].split()))
                if len(row) != t:
                    raise ValueError("Неверный размер матрицы F")
                for j in range(t):
                    self.f_table.setItem(i, j, QTableWidgetItem(str(row[j])))
                idx += 1
            
            # Матрица H (t строк, p столбцов)
            for i in range(t):
                row = list(map(int, lines[idx].split()))
                if len(row) != p:
                    raise ValueError("Неверный размер матрицы H")
                for j in range(p):
                    self.h_table.setItem(i, j, QTableWidgetItem(str(row[j])))
                idx += 1
            
            # Начальная разметка M0 (1 строка, p значений)
            row = list(map(int, lines[idx].split()))
            if len(row) != p:
                raise ValueError("Неверный размер M0")
            for i in range(p):
                self.m0_table.setItem(i, 0, QTableWidgetItem(str(row[i])))
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки файла: {str(e)}")
    
    def save_to_file(self):
        """Сохраняет матрицы в файл"""
        if not self.get_matrices_from_tables():
            return
        
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Text files (*.txt)")
            if not filename:
                return
            
            with open(filename, 'w') as f:
                p = self.F.shape[0]
                t = self.F.shape[1]
                f.write(f"{p} {t}\n")
                
                # Матрица F
                for i in range(p):
                    f.write(' '.join(map(str, self.F[i])) + '\n')
                
                # Матрица H
                for i in range(t):
                    f.write(' '.join(map(str, self.H[i])) + '\n')
                
                # M0
                f.write(' '.join(map(str, self.M0)) + '\n')
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения файла: {str(e)}")
    
    def get_matrices_from_tables(self):
        """Извлекает матрицы из таблиц"""
        try:
            # Матрица F
            rows_f = self.f_table.rowCount()
            cols_f = self.f_table.columnCount()
            self.F = np.zeros((rows_f, cols_f), dtype=int)
            
            for i in range(rows_f):
                for j in range(cols_f):
                    item = self.f_table.item(i, j)
                    if item:
                        self.F[i][j] = int(item.text())
            
            # Матрица H
            rows_h = self.h_table.rowCount()
            cols_h = self.h_table.columnCount()
            self.H = np.zeros((rows_h, cols_h), dtype=int)
            
            for i in range(rows_h):
                for j in range(cols_h):
                    item = self.h_table.item(i, j)
                    if item:
                        self.H[i][j] = int(item.text())
            
            # Начальная разметка
            rows_m = self.m0_table.rowCount()
            self.M0 = np.zeros(rows_m, dtype=int)
            
            for i in range(rows_m):
                item = self.m0_table.item(i, 0)
                if item:
                    self.M0[i] = int(item.text())
            
            # Матрица инцидентности C = H^T - F
            self.C = self.H.T - self.F
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при чтении матриц: {str(e)}")
            return False