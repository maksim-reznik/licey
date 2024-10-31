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
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

import matplotlib

SAVED_FILES_DIR = "saved_audio_files"


class MediaPlayerDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Медиаплеер")
        self.setGeometry(200, 200, 400, 150)
        self.setup_ui()

    def setup_ui(self):
        # Создаем медиаплеер
        self.media_player = QMediaPlayer()

        # Создаем основной layout
        main_layout = QtWidgets.QVBoxLayout()

        # Создаем контейнер для элементов управления
        control_layout = QtWidgets.QHBoxLayout()

        # Создаем и настраиваем кнопки
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(40, 40)
        self.stop_button = QPushButton("⬛")
        self.stop_button.setFixedSize(40, 40)

        # Создаем и настраиваем слайдер громкости
        self.volume_slider = QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)

        # Создаем слайдер прогресса
        self.progress_slider = QSlider(QtCore.Qt.Horizontal)
        self.progress_slider.setRange(0, 100)

        # Создаем метки времени
        self.time_label = QLabel("0:00 / 0:00")

        # Добавляем виджеты в контейнер управления
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(QtWidgets.QLabel("🔊"))
        control_layout.addWidget(self.volume_slider)

        # Добавляем все элементы в основной layout
        main_layout.addWidget(self.progress_slider)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.time_label, alignment=QtCore.Qt.AlignCenter)

        # Устанавливаем layout для диалога
        self.setLayout(main_layout)

        # Подключаем сигналы
        self.play_button.clicked.connect(self.play_pause)
        self.stop_button.clicked.connect(self.stop)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.progress_slider.sliderMoved.connect(self.set_position)

        # Подключаем сигналы медиаплеера
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.stateChanged.connect(self.media_state_changed)

    def set_audio(self, audio_segment):
        # Сохраняем временный файл для воспроизведения
        self.temp_path = os.path.join(SAVED_FILES_DIR, 'temp_playback.mp3')
        audio_segment.export(self.temp_path, format="mp3")
        self.media_player.setMedia(
            QMediaContent(QtCore.QUrl.fromLocalFile(self.temp_path)))

    def play_pause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop(self):
        self.media_player.stop()

    def change_volume(self, value):
        self.media_player.setVolume(value)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def position_changed(self, position):
        self.progress_slider.setValue(position)
        self.update_time_label()

    def duration_changed(self, duration):
        self.progress_slider.setRange(0, duration)
        self.update_time_label()

    def media_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("⏸")
        else:
            self.play_button.setText("▶")

    def update_time_label(self):
        position = self.media_player.position()
        duration = self.media_player.duration()
        self.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

    def format_time(self, ms):
        s = ms // 1000
        m = s // 60
        s = s % 60
        return f"{m}:{s:02d}"

    def closeEvent(self, event):
        self.media_player.stop()
        if hasattr(self, 'temp_path') and os.path.exists(self.temp_path):
            try:
                os.remove(self.temp_path)
            except:
                pass
        super().closeEvent(event)


class HistoryWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("История действий")
        self.setGeometry(200, 200, 400, 300)

        self.history_text = QtWidgets.QTextEdit(self)
        self.history_text.setReadOnly(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.history_text)

        self.close_button = QPushButton("Закрыть", self)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)


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

        self.history = []
        self.history_button = QPushButton("История", self)
        self.history_button.move(685, 517)
        self.history_button.resize(100, 30)
        self.history_button.clicked.connect(self.show_history)

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

        self.history = []
        self.history_button = QPushButton("История", self)
        self.history_button.move(685, 517)
        self.history_button.resize(100, 30)
        self.history_button.clicked.connect(self.show_history)

        self.graph_label = QLabel(self)
        self.graph_label.setGeometry(40, 580, 1120, 500)
        pixmap = QPixmap('audio_visualization.png')
        self.graph_label.setPixmap(pixmap)

        # В методе init_ui добавьте:
        self.help_btn = QPushButton(self)
        self.help_btn.setText("Справка")
        self.help_btn.move(465, 510)  # Измените координаты по необходимости
        self.help_btn.resize(170, 40)
        self.help_btn.clicked.connect(self.show_help)

        self.show()
        self.open_player_btn = QPushButton("Открыть медиаплеер", self)
        self.open_player_btn.move(40, 570)  # Настройте позицию под ваш интерфейс
        self.open_player_btn.resize(150, 30)
        self.open_player_btn.clicked.connect(self.show_media_player)

    def show_media_player(self):
        if hasattr(self, 'combined_audio'):
            self.media_player_dialog = MediaPlayerDialog(self)
            self.media_player_dialog.set_audio(self.combined_audio)
            self.media_player_dialog.show()
        else:
            self.console_update("Нет аудио для воспроизведения", is_error=True)

    def show_help(self):
        help_window = QtWidgets.QDialog(self)
        help_window.setWindowTitle("Справка")
        help_window.setGeometry(200, 200, 600, 400)

        # Создаем текстовое поле для описания
        help_text = QtWidgets.QTextEdit(help_window)
        help_text.setGeometry(20, 20, 560, 320)
        help_text.setReadOnly(True)

        # Описание функций
        description = """
        Описание функций программы:

        1. Добавить файл
        - Позволяет импортировать аудио файл в программу

        2. Экспортировать файл
        - Сохраняет готовую аудиодорожку в выбранное место на компьютере

        3. Добавить файл в конец аудиодорожки
        - Добавляет выбранный файл в конец текущей аудиодорожки

        4. Удалить последний файл с аудиодорожки
        - Удаляет последний добавленный аудио фрагмент

        5. Разделить выбранный файл
        - Разделяет выбранный аудио файл на две части в указанной точке

        Визуализация:
        - Верхний график показывает форму волны аудиодорожки
        - Нижний график показывает расположение сегментов в timeline
        """

        help_text.setText(description)

        # Кнопка закрытия
        close_button = QPushButton("Закрыть", help_window)
        close_button.setGeometry(250, 350, 100, 30)
        close_button.clicked.connect(help_window.close)

        help_window.exec_()

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
        self.audio_id[file_path.split('/')[-1]] = len(self.audio_files) + 1
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
            self.console_update(f"Файл {self.audio_files[self.used_ID].split('/')[-1]} добавлен в конец аудио-дорожки.")
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

            # Добавляем временную метку к именам файлов
            import time
            timestamp = int(time.time())
            part1_name = f"part1_{timestamp}_{self.used_name}"
            part2_name = f"part2_{timestamp}_{self.used_name}"

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
            # Определяем домашний каталог в зависимости от операционной системы
            if os.name == 'nt':  # для Windows
                default_path = os.path.expanduser('~\\Documents')
            else:  # для Linux и MacOS
                default_path = os.path.expanduser('~/Documents')

            # Открываем диалог выбора директории
            export_path = QtWidgets.QFileDialog.getSaveFileName(
                self,
                'Сохранить файл',
                default_path,  # используем определенный выше путь
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

    def truncate_filename(self, filename, max_length):
        # Разделяем имя файла и расширение
        name, ext = os.path.splitext(filename)

        if len(name) > max_length:
            return f"{name[:max_length]}...{ext}"
        return filename

    def console_update(self, txt):
        # Сохраняем сообщение в историю
        self.history.append(txt)

    def show_history(self):
        history_window = HistoryWindow(self)
        history_window.history_text.setText("\n".join(self.history))
        history_window.exec_()

    def on_item_clicked(self, item):
        self.used_name = item.text()
        self.used_ID = self.audio_id[self.used_name]
        display_name = self.truncate_filename(self.used_name, 20)
        self.file_inf.setText(f'ID: {self.used_ID}      Name: {display_name}')



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    # app.setStyleSheet('QTextEdit{background-image:url("yaratici.jpeg");}')
    app.setPalette(DarkPalette())
    editor = AudioEditor()
    app.exec_()
