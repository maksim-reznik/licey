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

SAVED_FILES_DIR = "saved_audio_files"


class AudioEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_files = {}
        self.audio_id = {}
        self.audio_segments = []
        self.audio_lengths = []
        self._create_output_directory()
        self._create_saved_files_directory()
        self._clean_output_directory()
        self.used_ID = 0
        self.used_name = ''
        self.init_ui()

    def init_ui(self):
        self.setGeometry(50, 50, 1200, 1100)

        self.list_files = QListWidget(self)
        self.list_files.resize(400, 470)
        self.list_files.move(40, 40)
        self.list_files.itemClicked.connect(self.on_item_clicked)

        self.import_btn = QPushButton(self)
        self.import_btn.setText('Добавить файл')
        self.import_btn.move(40, 510)
        self.import_btn.resize(200, 40)
        self.import_btn.clicked.connect(self.import_files)

        self.export_btn = QPushButton(self)
        self.export_btn.setText("Экспортировать файл")
        self.export_btn.move(240, 510)
        self.export_btn.resize(200, 40)
        self.export_btn.clicked.connect(self.export_final_file)

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
        self.file_inf.resize(500, 40)
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

        self.graph_label = QLabel(self)
        self.graph_label.setGeometry(40, 580, 1120, 500)
        pixmap = QPixmap('audio_visualization.png')
        self.graph_label.setPixmap(pixmap)

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
        self.list_files.addItem(file_path.split('/')[-1])
        self.audio_id[file_path.split('/')[-1]] = len(self.audio_files)
        self.audio_files[len(self.audio_files) + 1] = file_path
        shutil.copy(file_path, SAVED_FILES_DIR)

    def on_item_clicked(self, item):
        self.used_name = item.text()
        self.used_ID = self.audio_id[self.used_name]
        self.file_inf.setText(f'ID: {self.used_ID}      Name: {self.used_name}')

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

            # Создаём имена для новых файлов
            part1_name = f"part1_{self.used_name}"
            part2_name = f"part2_{self.used_name}"

            # Сохраняем файлы
            part1_path = os.path.join(SAVED_FILES_DIR, part1_name)
            part2_path = os.path.join(SAVED_FILES_DIR, part2_name)
            part1.export(part1_path, format="mp3")
            part2.export(part2_path, format="mp3")

            # Добавляем новые файлы в словарь audio_files
            new_id1 = len(self.audio_files) + 1
            new_id2 = len(self.audio_files) + 2
            self.audio_files[new_id1] = part1_path
            self.audio_files[new_id2] = part2_path

            # Добавляем новые файлы в словарь audio_id
            self.audio_id[part1_name] = new_id1
            self.audio_id[part2_name] = new_id2

            # Добавляем новые файлы в список QListWidget
            self.list_files.addItem(part1_name)
            self.list_files.addItem(part2_name)

            self.console_update(f"Файл {self.used_name} разделен на две части и добавлен в проект")
        else:
            self.console_update("Недействительный ID файла.")

    def visualize_audio(self):
        if hasattr(self, 'combined_audio'):
            data = np.array(self.combined_audio.get_array_of_samples())

            # Создаем фигуру и подграфики с темно-серым фоном
            fig, ax = plt.subplots(2, 1, figsize=(11.20, 5), facecolor='#1c1c1c')

            # Устанавливаем цвет фона для осей (светло-серый)
            for a in ax:
                a.set_facecolor('#333333')

            # График таймлайна
            ax[0].tick_params(axis='x', colors='white')
            ax[0].plot(data)  # Устанавливаем цвет линии
            ax[0].set_title('Горизонтальный таймлайн аудиодорожки', color='white')
            ax[0].set_xlabel('Время (сэмплы)', color='white')
            ax[0].set_yticks([])  # Скрыть метки по оси Y для ясности
            ax[0].grid(True)  # Устанавливаем цвет сеткиpyunproject

            # Горизонтальная столбчатая диаграмма для сегментов аудиодорожки
            colors = list(mcolors.TABLEAU_COLORS.values())
            for i, segment in enumerate(self.audio_segments):
                color = colors[i % len(colors)]
                ax[1].barh(0, segment['end'] - segment['start'], left=segment['start'], height=0.1,
                           color=color, label=f"File {i + 1}: {segment['name']}")
            ax[1].tick_params(axis='x', colors='white')
            ax[1].set_title('Сегменты аудиодорожки', color='white')
            ax[1].set_xlabel('Время (сэмплы)', color='white')
            ax[1].set_yticks([])  # Скрыть метки по оси Y
            ax[1].set_ylim(-0.2, 0.2)  # Установить пределы по оси Y
            ax[1].legend(bbox_to_anchor=(0, -0.3), loc='upper left', ncol=4, facecolor='gray')

            plt.tight_layout()
            output_image_path = os.path.join(SAVED_FILES_DIR, 'audio_visualization.png')
            plt.savefig(output_image_path)
            pixmap = QPixmap('saved_audio_files/audio_visualization.png')
            self.graph_label.setPixmap(pixmap)
    def play_audio(self):
        if hasattr(self, 'combined_audio'):
            playback.play(self.combined_audio)
        else:
            self.console_update("Нет комбинированной аудиодорожки.")

    def export_final_file(self):
        if hasattr(self, 'combined_audio'):
            # Открываем диалог выбора директории
            export_path = QtWidgets.QFileDialog.getSaveFileName(
                self,
                'Сохранить файл',
                '/',
                'Audio Files (*.mp3)'
            )[0]

            if export_path:  # Если путь был выбран
                try:
                    self.combined_audio.export(export_path, format="mp3")
                    self.console_update(f"Файл успешно экспортирован как {export_path}")
                except Exception as e:
                    self.console_update(f"Ошибка при экспорте файла: {str(e)}")
            else:
                self.console_update("Экспорт отменён")
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
