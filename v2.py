import os
import shutil
from PyQt5.QtWidgets import QPushButton, QSlider
from darktheme.widget_template import DarkApplication, DarkPalette
from pydub import AudioSegment, playback
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from PyQt5.QtWidgets import QListWidget, QLabel, QPushButton, QSlider
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtGui import QPixmap
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import matplotlib
matplotlib.use('Qt5Agg')

class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

SAVED_FILES_DIR = "saved_audio_files"


class AudioEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_files = {}
        self.audio_segments = []
        self.audio_lengths = []
        self._create_output_directory()
        self._create_saved_files_directory()
        self._clean_output_directory()
        self.used_ID = 0
        self.used_name = ''
        self.init_ui()

    def init_ui(self):
        self.setGeometry(150, 150, 1200, 1000)

        self.list_files = QListWidget(self)
        self.list_files.resize(400, 500)
        self.list_files.move(40, 40)

        # Для красоты
        self.file_inf_beauty = QListWidget(self)
        self.file_inf_beauty.resize(700, 60)
        self.file_inf_beauty.move(460, 40)

        self.add_file_beauty = QListWidget(self)
        self.add_file_beauty.resize(700, 80)
        self.add_file_beauty.move(460, 120)

        self.remove_file_beauty = QListWidget(self)
        self.remove_file_beauty.resize(700, 80)
        self.remove_file_beauty.move(460, 220)

        self.split_file_beauty = QListWidget(self)
        self.split_file_beauty.resize(700, 160)
        self.split_file_beauty.move(460, 320)

        self.console_beauty = QListWidget(self)
        self.console_beauty.resize(500, 60)
        self.console_beauty.move(660, 500)

        # Конец красоты

        self.file_inf = QLabel(self)
        self.file_inf.setText(f'ID: {None}      Name: {None}')
        self.file_inf.move(500, 50)
        self.file_inf.resize(300, 40)
        self.file_inf.setStyleSheet("QLabel{font-size: 15pt;}")

        self.add_file = QLabel(self)
        self.add_file.setText('Добавить файл в конец аудиодорожки')
        self.add_file.move(500, 108)
        self.add_file.resize(500, 100)
        self.add_file.setStyleSheet("QLabel{font-size: 15pt;}")

        self.add_btn = QPushButton(self)
        self.add_btn.move(970, 145)
        self.add_btn.resize(170, 30)
        self.add_btn.setText('Нажмите для действия')
        self.add_btn.clicked.connect(self.add_file_to_end)

        self.remove_file = QLabel(self)
        self.remove_file.setText('Удалить последний файл с аудиодорожки')
        self.remove_file.move(500, 210)
        self.remove_file.resize(500, 100)
        self.remove_file.setStyleSheet("QLabel{font-size: 15pt;}")

        self.remove_btn = QPushButton(self)
        self.remove_btn.move(970, 245)
        self.remove_btn.resize(170, 30)
        self.remove_btn.setText('Нажмите для действия')
        self.remove_btn.clicked.connect(self.remove_last_file)

        self.split_file_txt = QLabel(self)
        self.split_file_txt.setText("Разделить выбранный файл")
        self.split_file_txt.move(500, 310)
        self.split_file_txt.resize(500, 100)
        self.split_file_txt.setStyleSheet("QLabel{font-size: 15pt;}")

        self.split_btn = QPushButton(self)
        self.split_btn.move(970, 345)
        self.split_btn.resize(170, 30)
        self.split_btn.setText('Нажмите для действия')
        self.split_btn.clicked.connect(self.split_file)

        self.split_slider = QSlider(QtCore.Qt.Orientation.Horizontal, self)
        self.split_slider.setRange(0, 10)
        # self.split_slider.setRange(0, self.audio_lengths[self.used_ID])
        self.split_slider.move(500, 385)
        self.split_slider.resize(400, 50)

        self.split_txt = QLabel(self)
        self.split_txt.setText('Укажите время разделения')
        self.split_txt.move(530, 420)
        self.split_txt.resize(200, 20)

        self.console = QLabel(self)
        self.console.setText('Запуск программы')
        self.console.setStyleSheet("QLabel{font-size: 11pt;}")
        self.console.move(685, 517)
        self.console.resize(4000, 20)

        self.canvas = MplCanvas(self, width=7, height=4, dpi=100)

        self.graph_label = QLabel(self)
        self.graph_label.setGeometry(600, 40, 700, 400)

        self.show()

    def _create_output_directory(self):
        if not os.path.exists(SAVED_FILES_DIR):
            os.makedirs(SAVED_FILES_DIR)

    def _create_saved_files_directory(self):
        if not os.path.exists(SAVED_FILES_DIR):
            os.makedirs(SAVED_FILES_DIR)

    def _clean_output_directory(self):
        for filename in os.listdir(SAVED_FILES_DIR):
            file_path = os.path.join(SAVED_FILES_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Error deleting file {file_path}. Reason: {e}')

    def import_files(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName()[0]
        self.audio_files[len(self.audio_files) + 1] = file_path
        shutil.copy(file_path, SAVED_FILES_DIR)

    def add_file_to_end(self):
        if self.used_ID in self.audio_files:
            audio_to_add = AudioSegment.from_file(self.audio_files[self.used_ID])
            start = len(self.combined_audio) if hasattr(self, 'combined_audio') else 0
            end = start + len(audio_to_add)
            self.audio_segments.append({
                'start': start,
                'end': end,
                'name': os.path.basename(self.audio_files[self.used_ID])
            })
            self.audio_lengths.append(len(audio_to_add))
            if hasattr(self, 'combined_audio'):
                self.combined_audio += audio_to_add
            else:
                self.combined_audio = audio_to_add
            self.console_update(f"Файл {self.audio_files[self.used_ID]} добавлен в конец аудио-дорожки.")
            self.visualize_audio()
        else:
            self.console_update("Недействительный ID файла.")

    def remove_last_file(self):
        if hasattr(self, 'combined_audio') and self.combined_audio:
            if self.audio_lengths:
                last_length = self.audio_lengths.pop()
                self.combined_audio = self.combined_audio[:-last_length]
                self.audio_segments.pop(-1)
                self.console_update("Последний файл удален.")
                self.visualize_audio()
            else:
                self.console_update("Нет файлов для удаления.")
        else:
            self.console_update("Нет файлов для удаления.")

    def split_file(self):
        if self.used_ID in self.audio_files:
            audio = AudioSegment.from_file(self.audio_files[self.used_ID])
            split_time_ms = self.split_slider.value() * 1000
            part1 = audio[:split_time_ms]
            part2 = audio[split_time_ms:]
            part1_path = os.path.join(SAVED_FILES_DIR, f"part1_{self.audio_files[self.used_ID].split('/')[-1]}")
            part2_path = os.path.join(SAVED_FILES_DIR, f"part2_{self.audio_files[self.used_ID].split('/')[-1]}")
            part1.export(part1_path, format="mp3")
            part2.export(part2_path, format="mp3")
            self.audio_files[len(self.audio_files) + 1] = part1_path
            self.audio_files[len(self.audio_files) + 1] = part2_path
            self.console_update(f"Файл {self.audio_files[self.used_ID]} разделен на две части.")
        else:
            self.console_update("Недействительный ID файла.")

    def visualize_audio(self):
        if not hasattr(self, 'combined_audio'):
            return

        # Создаем новую фигуру
        fig = Figure(figsize=(7, 4), dpi=100)
        axes = fig.add_subplot(111)

        # Получаем данные аудио в виде массива
        audio_array = np.array(self.combined_audio.get_array_of_samples())

        # Создаем временную шкалу (в секундах)
        time = np.linspace(0, len(self.combined_audio) / 1000, len(audio_array))

        # Строим график амплитуды
        axes.plot(time, audio_array, color='lightblue', alpha=0.5, linewidth=0.5)

        # Добавляем разделители сегментов
        for segment in self.audio_segments:
            start_time = segment['start'] / 1000
            end_time = segment['end'] / 1000

            # Добавляем горизонтальную линию для сегмента
            axes.hlines(y=0, xmin=start_time, xmax=end_time,
                        color='red', linewidth=2)

            # Добавляем название сегмента
            middle_point = (start_time + end_time) / 2
            axes.text(middle_point, -max(audio_array) * 0.5,
                      segment['name'],
                      rotation=45,
                      ha='right')

        # Настройка графика
        axes.set_xlabel('Время (секунды)')
        axes.set_ylabel('Амплитуда')
        axes.set_title('Визуализация аудио')
        axes.grid(True, alpha=0.3)

        # Сохраняем график как изображение
        graph_path = os.path.join(SAVED_FILES_DIR, 'current_visualization.png')
        fig.savefig(graph_path, bbox_inches='tight', dpi=100)

        # Загружаем изображение в QLabel
        pixmap = QtGui.QPixmap(graph_path)
        # Масштабируем изображение под размер QLabel
        scaled_pixmap = pixmap.scaled(self.graph_label.size(),
                                      QtCore.Qt.KeepAspectRatio,
                                      QtCore.Qt.SmoothTransformation)
        self.graph_label.setPixmap(scaled_pixmap)

        # Закрываем фигуру для освобождения памяти
        plt.close(fig)

    def play_audio(self):
        if hasattr(self, 'combined_audio'):
            playback.play(self.combined_audio)
        else:
            self.console_update("Нет комбинированной аудиодорожки.")

    def export_final_file(self, filename="final_output.mp3"):
        if hasattr(self, 'combined_audio'):
            output_file_path = os.path.join(SAVED_FILES_DIR, filename)
            self.combined_audio.export(output_file_path, format="mp3")
            self.console_update(f"Файл экспортирован как {output_file_path}.")
        else:
            self.console_update("Нет комбинированной аудиодорожки для экспорта.")

    def console_update(self, txt):
        self.console.setText(txt)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    # app.setStyleSheet('QTextEdit{background-image:url("yaratici.jpeg");}')
    app.setPalette(DarkPalette())
    editor = AudioEditor()
    app.exec_()
