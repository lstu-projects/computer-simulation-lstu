# animation_mixins.py

import random
from PyQt5.QtWidgets import QMessageBox
from matplotlib.animation import FuncAnimation
import numpy as np

class AnimationMixin:
    def initialize_visualization(self):
        """Инициализирует визуализацию сети"""
        if not self.get_matrices_from_tables():
            return
        
        # Создаем копию начальной разметки
        self.current_marking = self.M0.copy() if self.M0 is not None else None
        
        if self.current_marking is None:
            QMessageBox.warning(self, "Ошибка", "Начальная разметка не определена!")
            return
            
        self.update_transition_combo()
        self.visualize_network()
        self.update_state_info()
    
    def update_transition_combo(self):
        """Обновляет список переходов в комбобоксе"""
        self.transition_combo.clear()
        self.transition_combo.addItem("Автоматический выбор")
        
        if self.H is not None:
            for i in range(self.H.shape[0]):
                self.transition_combo.addItem(f"T{i+1}")
    
    def get_enabled_transitions(self, marking=None):
        """Возвращает список разрешенных переходов"""
        if marking is None:
            marking = self.current_marking
        
        if marking is None or self.F is None:
            return []
        
        enabled = []
        for t in range(self.H.shape[0]):
            can_fire = True
            for p in range(len(marking)):
                if marking[p] < self.F[p][t]:
                    can_fire = False
                    break
            if can_fire:
                # Дополнительная проверка: переход должен иметь хотя бы один вход или выход
                has_connection = False
                for p in range(len(marking)):
                    if self.F[p][t] > 0 or self.H[t][p] > 0:
                        has_connection = True
                        break
                if has_connection:
                    enabled.append(t)
        return enabled
    
    def fire_transition(self, transition_idx, marking=None):
        """Срабатывает переход и возвращает новую разметку"""
        if marking is None:
            marking = self.current_marking
        
        if marking is None or self.F is None or self.H is None:
            return None
        
        # Проверяем границы индексов
        if transition_idx < 0 or transition_idx >= self.H.shape[0]:
            return None
        
        new_marking = marking.copy()
        
        # Проверяем, можем ли сработать переход
        for p in range(len(marking)):
            if marking[p] < self.F[p][transition_idx]:
                return None  # Переход не может сработать
        
        # Применяем правило срабатывания
        for p in range(len(new_marking)):
            new_marking[p] = marking[p] - self.F[p][transition_idx] + self.H[transition_idx][p]
        
        return new_marking
    
    def start_animation(self):
        """Запускает анимацию"""
        if self.current_marking is None:
            self.initialize_visualization()
        
        if self.current_marking is None:
            QMessageBox.warning(self, "Ошибка", "Не удалось инициализировать визуализацию!")
            return
        
        self.animation_running = True
        self.start_animation_btn.setEnabled(False)
        self.stop_animation_btn.setEnabled(True)
        
        self.animation_timer.start(self.animation_speed)
    
    def stop_animation(self):
        """Останавливает анимацию"""
        self.animation_running = False
        self.animation_timer.stop()
        self.start_animation_btn.setEnabled(True)
        self.stop_animation_btn.setEnabled(False)
    
    def reset_animation(self):
        """Сбрасывает анимацию к начальному состоянию"""
        self.stop_animation()
        if self.M0 is not None:
            self.current_marking = self.M0.copy()
            self.visualize_network()
            self.update_state_info()
    
    def animation_step(self):
        """Выполняет один шаг анимации"""
        if not self.animation_running:
            return
        
        enabled_transitions = self.get_enabled_transitions()
        
        if not enabled_transitions:
            # Нет разрешенных переходов - перезапускаем анимацию с начальной разметки
            self.reset_animation()
            self.start_animation()
            return
        
        # Выбираем случайный переход
        selected_transition = random.choice(enabled_transitions)
        
        # Срабатываем переход
        new_marking = self.fire_transition(selected_transition)
        
        if new_marking is not None:
            self.animate_transition_firing(selected_transition, new_marking)
    
    def fire_selected_transition(self):
        """Срабатывает выбранный переход"""
        if self.transition_combo.currentIndex() == 0:  # Автоматический выбор
            enabled_transitions = self.get_enabled_transitions()
            if not enabled_transitions:
                QMessageBox.warning(self, "Предупреждение", "Нет разрешенных переходов!")
                return
            selected_transition = random.choice(enabled_transitions)
        else:
            selected_transition = self.transition_combo.currentIndex() - 1
            enabled_transitions = self.get_enabled_transitions()
            if selected_transition not in enabled_transitions:
                QMessageBox.warning(self, "Предупреждение", f"Переход T{selected_transition+1} не разрешен!")
                return
        
        new_marking = self.fire_transition(selected_transition)
        if new_marking is not None:
            self.animate_transition_firing(selected_transition, new_marking)
    
    def animate_transition_firing(self, transition_idx, new_marking):
        """Анимирует срабатывание перехода"""
        if self.ani:
            self.ani.event_source.stop()
            self.ani = None
        
        old_marking = self.current_marking.copy()
        self.current_marking = new_marking
        self.update_state_info()
        
        frames = 40  # Увеличили количество кадров для более плавной анимации
        phase_frames = frames // 2
        
        def update(frame):
            if frame < phase_frames:
                input_frac = frame / phase_frames
                output_frac = 0
            else:
                input_frac = 1
                output_frac = (frame - phase_frames) / phase_frames
            
            frac = (input_frac + output_frac) / 2
            color_frac = np.abs(np.sin(np.pi * frac))
            highlight_color = (1, 0.5 + 0.5 * color_frac, 0.5 + 0.5 * color_frac)
            
            self.visualize_network(highlight_transition=transition_idx, 
                                highlight_color=highlight_color, 
                                input_frac=input_frac, 
                                output_frac=output_frac, 
                                old_marking=old_marking)
            
            if frame == frames - 1:
                self.ani.event_source.stop()
                self.ani = None
                self.visualize_network()
        
        self.ani = FuncAnimation(self.figure, update, frames=frames, blit=False, interval=30, repeat=False)
        self.ani._init_draw()  # Чтобы избежать предупреждения
        
    def change_animation_speed(self, value):
        """Изменяет скорость анимации"""
        self.animation_speed = value
        self.speed_label.setText(f"{value/1000:.1f}s")
        if self.animation_running:
            self.animation_timer.setInterval(value)
    
    def update_state_info(self):
        """Обновляет информацию о текущем состоянии"""
        if self.current_marking is not None:
            marking_str = str(self.current_marking)
            self.current_state_label.setText(f"Текущая разметка: {marking_str}")
            
            enabled_transitions = self.get_enabled_transitions()
            if enabled_transitions:
                enabled_str = ", ".join([f"T{t+1}" for t in enabled_transitions])
                self.enabled_transitions_label.setText(f"Разрешенные переходы: {enabled_str}")
            else:
                self.enabled_transitions_label.setText("Разрешенные переходы: нет (тупиковая разметка)")