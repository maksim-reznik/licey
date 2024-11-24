import os  # Модуль для работы с файловой системой
import shutil  # Модуль для операций с файлами и директориями
import threading  # Модуль для работы с потоками
import pygame  # Модуль для работы с аудио
import tempfile  # Модуль для создания временных файлов
import time  # Модуль для работы с временем
from multiprocessing import Process  # Модуль для работы с процессами

import numpy as np  # Модуль для работы с массивами
from pydub import AudioSegment  # Модуль для работы с аудиофайлами
from pydub.playback import play  # Модуль для воспроизведения аудио

from PyQt5 import QtCore, QtGui, QtWidgets, Qt  # Импортируем модули для создания GUI
from PyQt5.QtWidgets import (
    QPushButton,
    QSlider,
    QMessageBox,
    QListWidget,
    QLabel
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent  # Модули для работы с мультимедиа
from PyQt5.QtMultimediaWidgets import QVideoWidget  # Модуль для отображения видео
from darktheme.widget_template import DarkApplication, DarkPalette  # Импортируем темы

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, \
    NavigationToolbar2QT as NavigationToolbar  # Импортируем модули для работы с графиками
from matplotlib.figure import Figure  # Модуль для создания фигур
import matplotlib.pyplot as plt  # Модуль для построения графиков
import matplotlib.colors as mcolors  # Модуль для работы с цветами

font = QtGui.QFont('Arial', 15)  # Устанавливаем шрифт для текста
SAVED_FILES_DIR = "saved_audio_files"  # Директория для сохраненных аудиофайлов

class HistoryWindow(QtWidgets.QDialog):  # Класс для окна истории действий
    def __init__(self, parent=None):  # Конструктор класса
        super().__init__(parent)  # Вызов конструктора родительского класса
        self.setWindowTitle("История действий")  # Заголовок окна
        self.setGeometry(200, 200, 400, 300)  # Установка размеров окна

        self.history_text = QtWidgets.QTextEdit(self)  # Поле для отображения текста истории
        self.history_text.setReadOnly(True)  # Установка поля как только для чтения

        layout = QtWidgets.QVBoxLayout(self)  # Вертикальный компоновщик
        layout.addWidget(self.history_text)  # Добавление текстового поля в компоновщик

        self.close_button = QPushButton("Закрыть", self)  # Кнопка закрытия окна
        self.close_button.clicked.connect(self.close)  # Подключение сигнала нажатия к методу закрытия
        layout.addWidget(self.close_button)  # Добавление кнопки в компоновщик

class AudioEditor(QtWidgets.QMainWindow):  # Класс основного окна редактора аудио
    def __init__(self):  # Конструктор класса
        super().__init__()  # Вызов конструктора родительского класса
        pygame.mixer.init()  # Инициализация модуля Pygame для работы с аудио
        self.is_playing = 0  # Переменная для отслеживания состояния воспроизведения
        self.audio_finished_event = pygame.USEREVENT + 1  # Создаем уникальное событие для окончания воспроизведения
        pygame.mixer.music.set_endevent(self.audio_finished_event)  # Устанавливаем событие окончания воспроизведения
        self.items = []  # Список для хранения элементов
        self.is_playing = None  # Переменная для состояния воспроизведения
        self.screen_size = self.get_screen_size()  # Получение размера экрана
        # Настройка коэффициента модификации в зависимости от высоты экрана
        if self.screen_size[1] >= 2000:
            self.mod = 1.5
        elif self.screen_size[1] >= 1200:
            self.mod = 1
        elif self.screen_size[1] >= 1080:
            self.mod = 0.85
        else:
            self.mod = 0.5

        self.audio_files = {}  # Словарь для хранения аудиофайлов
        self.audio_id = {}  # Словарь для хранения идентификаторов ауд иофайлов
        self.audio_segments = []  # Список для хранения сегментов аудио
        self.audio_lengths = []  # Список для хранения длин аудиофайлов
        self.volume_x = []  # Список для хранения значений громкости
        self.volume_slid = 0  # Переменная для хранения текущего значения громкости
        self._create_output_directory()  # Создание директории для выходных файлов
        self._create_saved_files_directory()  # Создание директории для сохраненных файлов
        self._clean_output_directory()  # Очистка выходной директории
        self.used_ID = 0  # Переменная для хранения текущего ID
        self.used_name = ''  # Переменная для хранения текущего имени файла
        self.init_ui()  # Инициализация пользовательского интерфейса

        self.history = []  # Список для хранения истории действий
        self.history_button = QPushButton("История", self)  # Кнопка для открытия истории
        self.history_button.move(int(685 * self.mod), int(517 * self.mod))  # Установка позиции кнопки
        self.history_button.resize(int(100 * self.mod), int(30 * self.mod))  # Установка размера кнопки
        self.history_button.clicked.connect(self.show_history)  # Подключение сигнала нажатия к методу показа истории
        self.history_button.setStyleSheet("QLabel{font-size:" + str(15 * self.mod) + "pt;}")  # Установка стиля кнопки

    def get_screen_size(self):  # Метод для получения размера экрана
        screen = QtWidgets.QApplication.primaryScreen()  # Получаем основной экран
        screen_size = screen.size()  # Получаем размер экрана
        return screen_size.width(), screen_size.height()  # Возвращаем ширину и высоту экрана

    def init_ui(self):  # Метод для инициализации пользовательского интерфейса
        self.setGeometry(int(50 * self.mod), int(50 * self.mod), int(1250 * self.mod), int(1100 * self.mod))  # Установка размеров окна

        self.list_files = QListWidget(self)  # Список для отображения загруженных файлов
        self.list_files.resize(int(400 * self.mod), int(470 * self.mod))  # Установка размера списка
        self.list_files.move(int(40 * self.mod), int(40 * self.mod))  # Установка позиции списка
        self.list_files.itemClicked.connect(self.on_item_clicked)  # Подключение сигнала нажатия на элемент списка
        self.list_files.setStyleSheet("QLabel{font-size:" + str(int(15 * self.mod)) + "pt;}")  # Установка стиля списка

        self.import_btn = QPushButton(self)  # Кнопка для импорта файлов
        self.import_btn.setText('Добавить файл')  # Установка текста кнопки
        self.import_btn.move(int(40 * self.mod), int(510 * self.mod))  # Установка позиции кнопки
        self.import_btn.resize(int(200 * self.mod), int(40 * self.mod))  # Установка размера кнопки
        self.import_btn.clicked.connect(self.import_files)  # Подключение сигнала нажатия к методу импорта файлов
        self.import_btn.setStyleSheet("QPushButton{font-size:" + str(int(12 * self.mod)) + "pt;}")  # Установка стиля кнопки

        self.export_btn = QPushButton(self)  # Кнопка для экспорта файлов
        self.export_btn.setText("Экспортировать файл")  # Установка текста кнопки
        self.export_btn.move(int(240 * self.mod), int(510 * self.mod))  # Установка позиции кнопки
        self.export_btn.resize(int(200 * self.mod), int(40 * self.mod))  # Установка размера кнопки
        self.export_btn.clicked.connect(self.export_final_file)  # Подключение сигнала нажатия к методу экспорта файлов
        self.export_btn.setStyleSheet("QPushButton{font-size:" + str(int(12 * self.mod)) + "pt;}")  # Установка стиля кнопки

        # Создание дополнительных элементов интерфейса для улучшения визуального восприятия
        self.file_inf_beauty = QListWidget(self)  # Список для отображения информации о файлах
        self.file_inf_beauty.resize(int(700 * self.mod), int(60 * self.mod))  # Установка размера списка
        self.file_inf_beauty .move(int(460 * self.mod), int(40 * self.mod))  # Установка позиции списка

        self.volume_beauty = QListWidget(self)  # Список для отображения громкости
        self.volume_beauty.resize(int(60 * self.mod), int(510 * self.mod))  # Установка размера списка
        self.volume_beauty.move(int(1175 * self.mod), int(295 * self.mod))  # Установка позиции списка

        self.add_file_beauty = QListWidget(self)  # Список для отображения добавленных файлов
        self.add_file_beauty.resize(int(700 * self.mod), int(80 * self.mod))  # Установка размера списка
        self.add_file_beauty.move(int(460 * self.mod), int(120 * self.mod))  # Установка позиции списка

        self.remove_file_beauty = QListWidget(self)  # Список для отображения удаленных файлов
        self.remove_file_beauty.resize(int(700 * self.mod), int(80 * self.mod))  # Установка размера списка
        self.remove_file_beauty.move(int(460 * self.mod), int(220 * self.mod))  # Установка позиции списка

        self.split_file_beauty = QListWidget(self)  # Список для отображения разделенных файлов
        self.split_file_beauty.resize(int(700 * self.mod), int(160 * self.mod))  # Установка размера списка
        self.split_file_beauty.move(int(460 * self.mod), int(320 * self.mod))  # Установка позиции списка

        self.console_beauty = QListWidget(self)  # Список для отображения консольных сообщений
        self.console_beauty.resize(int(500 * self.mod), int(60 * self.mod))  # Установка размера списка
        self.console_beauty.move(int(660 * self.mod), int(500 * self.mod))  # Установка позиции списка

        # Конец создания дополнительных элементов интерфейса
        self.file_inf = QLabel(self)  # Метка для отображения информации о файле
        self.file_inf.setText(f'ID: {None}      Name: {None}')  # Установка текста метки
        self.file_inf.move(int(500 * self.mod), int(50 * self.mod))  # Установка позиции метки
        self.file_inf.resize(int(500 * self.mod), int(40 * self.mod))  # Установка размера метки
        self.file_inf.setStyleSheet("QLabel{font-size:" + str(int(15 * self.mod)) + "pt;}")  # Установка стиля метки

        self.add_file = QLabel(self)  # Метка для добавления файла
        self.add_file.setText('Добавить файл в конец аудиодорожки')  # Установка текста метки
        self.add_file.move(int(500 * self.mod), int(108 * self.mod))  # Установка позиции метки
        self.add_file.resize(int(500 * self.mod), int(100 * self.mod))  # Установка размера метки
        self.add_file.setStyleSheet("QLabel{font-size:" + str(int(15 * self.mod)) + "pt;}")  # Установка стиля метки

        self.add_btn = QPushButton(self)  # Кнопка для добавления файла в конец аудиодорожки
        self.add_btn.move(int(970 * self.mod), int(145 * self.mod))  # Установка позиции кнопки
        self.add_btn.resize(int(170 * self.mod), int(30 * self.mod))  # Установка размера кнопки
        self.add_btn.setText('Нажмите для действия')  # Установка текста кнопки
        self.add_btn.clicked.connect(self.add_file_to_end)  # Подключение сигнала нажатия к методу добавления файла
        self.add_btn.setStyleSheet("QPushButton{font-size:" + str(int(10 * self.mod)) + "pt;}")  # Установка стиля кнопки

        self.remove_file = QLabel(self)  # Метка для удаления файла
        self.remove_file.setText('Удалить последний файл с аудиодорожки')  # Установка текста метки
        self.remove_file.move(int(500 * self.mod), int(210 * self.mod))  # Установка позиции метки
        self.remove_file.resize(int(500 * self.mod), int(100 * self.mod))  # Установка размера метки
        self.remove_file.setStyleSheet("QLabel{font-size:" + str(int(15 * self.mod)) + "pt;}")  # У становка стиля метки

        self.remove_btn = QPushButton(self)  # Кнопка для удаления последнего файла
        self.remove_btn.move(int(970 * self.mod), int(245 * self.mod))  # Установка позиции кнопки
        self.remove_btn.resize(int(170 * self.mod), int(30 * self.mod))  # Установка размера кнопки
        self.remove_btn.setText('Нажмите для действия')  # Установка текста кнопки
        self.remove_btn.clicked.connect(self.remove_last_file)  # Подключение сигнала нажатия к методу удаления файла
        self.remove_btn.setStyleSheet("QPushButton{font-size:" + str(int(10 * self.mod)) + "pt;}")  # Установка стиля кнопки

        self.split_file_txt = QLabel(self)  # Метка для разделения файла
        self.split_file_txt.setText("Разделить выбранный файл")  # Установка текста метки
        self.split_file_txt.move(int(500 * self.mod), int(310 * self.mod))  # Установка позиции метки
        self.split_file_txt.resize(int(500 * self.mod), int(100 * self.mod))  # Установка размера метки
        self.split_file_txt.setStyleSheet("QLabel{font-size:" + str(int(15 * self.mod)) + "pt;}")  # Установка стиля метки

        self.split_btn = QPushButton(self)  # Кнопка для разделения файла
        self.split_btn.move(int(970 * self.mod), int(345 * self.mod))  # Установка позиции кнопки
        self.split_btn.resize(int(170 * self.mod), int(30 * self.mod))  # Установка размера кнопки
        self.split_btn.setText('Нажмите для действия')  # Установка текста кнопки
        self.split_btn.clicked.connect(self.split_file)  # Подключение сигнала нажатия к методу разделения файла
        self.split_btn.setStyleSheet("QPushButton{font-size:" + str(int(10 * self.mod)) + "pt;}")  # Установка стиля кнопки

        self.split_slider = QSlider(QtCore.Qt.Orientation.Horizontal, self)  # Ползунок для указания времени разделения
        self.split_slider.setRange(0, 10)  # Установка диапазона ползунка
        self.split_slider.move(int(500 * self.mod), int(385 * self.mod))  # Установка позиции ползунка
        self.split_slider.resize(int(400 * self.mod), int(50 * self.mod))  # Установка размера ползунка
        self.split_slider.setStyleSheet("QLabel{font-size:" + str(int(15 * self.mod)) + "pt;}")  # Установка стиля ползунка

        self.split_txt = QLabel(self)  # Метка для указания времени разделения
        self.split_txt.setText('Укажите время разделения')  # Установка текста метки
        self.split_txt.move(int(530 * self.mod), int(420 * self.mod))  # Установка позиции метки
        self.split_txt.resize(int(400 * self.mod), int(20 * self.mod))  # Установка размера метки
        self.split_txt.setStyleSheet("QLabel{font-size:" + str(int(15 * self.mod)) + "pt;}")  # Установка стиля метки

        self.history = []  # Список для хранения истории действий
        self.history_button = QPushButton("История", self)  # Кнопка для открытия истории
        self.history_button.move(int(685 * self.mod), int(517 * self.mod))  # Установка позиции кнопки
        self.history_button.resize(int(100 * self.mod), int(30 * self.mod))  # Установка размера кнопки
        self.history_button.clicked.connect(self.show_history)  # Подключение сигнала нажатия к методу показа истории
        self.history_button.setStyleSheet("QPushButton{font-size:" + str(int(12 * self.mod)) + "pt;}")  # Установка стиля кнопки

        self.graph_label = QLabel(self)  # Метка для отображения графика
        self.graph_label.setGeometry(int(40 * self.mod), int(580 * self.mod), int(1120 * self.mod), int(500 * self.mod))  # Установка размеров метки
        pixmap = QtGui.QPixmap('audio_visualization.png')  # Загружаем изображение графика
        self.graph_label.setScaledContents(True)  # Устанавливаем масштабирование содержимого
        self.graph_label.setPixmap(pixmap)  # Устанавливаем загруженное изображение в метку

        self.help_btn = QPushButton(self)  # Кнопка для открытия справки
        self.help_btn.setText("Справка")  # Установка текста кнопки
        self.help_btn.move(int(465 * self.mod), int(510 * self.mod))  # Установка позиции кнопки
        self.help_btn.resize(int(170 * self.mod), int(40 * self.mod))  # Установка размера кнопки
        self.help_btn.clicked.connect(self.show_help)  # Подключение сигнала нажатия к методу показа справки
        self.help_btn.setStyleSheet("QPushButton{font-size:" + str(int(12 * self.mod)) + "pt;}")  # Установка стиля кнопки

        # Кнопка воспроизведения/остановки
        self.play_button = QPushButton("🞂", self)  # Кнопка для воспроизведения
        self.play_button.move(int(1170 * self.mod), int(40 * self.mod))  # Установка позиции кнопки
        self.play_button.resize(int(70 * self.mod), int(70 * self.mod))  # Установка размера кнопки
        self.play_button.setStyleSheet("QPushButton{font-size:" + str(int(15 * self.mod)) + "pt;}")  # Установка стиля кнопки
        self.play_button.clicked.connect(self.play_pause_audio)  # Подключение сигнала нажатия к методу воспроизведения/остановки

        self.stop_button = QPushButton("■", self)  # Кнопка для остановки воспроизведения
        self.stop_button.move(int(1170 * self.mod), int(120 * self.mod))  # Установка позиции кнопки
        self.stop_button.resize(int(70 * self.mod), int(70 * self.mod))  # Установка размера кнопки
        self.stop_button.setStyleSheet("QPushButton{font-size:" + str(int(14 * self.mod)) + "pt;}")  # Установка стиля кнопки
        self.stop_button.clicked.connect(self.stop_audio)  # Подключение сигнала нажатия к методу остановки воспроизведения

        # Ползунок громкости
        self.volume_slider = QSlider(QtCore.Qt.Vertical, self)  # Ползунок для регулировки громкости
        self.volume_slider.setRange(-10, 10)  # Установка диапазона ползунка
        self.volume_slider.setValue(0)  # Установка значения громкости по умолчанию на 100%
        self.volume_slider.move(int(1157 * self.mod), int(340 * self.mod))  # Установка позиции ползунка
        self.volume_slider.resize(int(100 * self.mod), int(400 * self.mod))  # Установка размера ползунка
        self.volume_slider.valueChanged.connect(self.set_volume)  # Подключение сигнала изменения значения ползунка к методу установки громкости

        # Значок громкости
        self.volume_label = QLabel(self)  # Метка для отображения значка громкости
        self.volume_label.setText('🔊')  # Установка текста метки
        self.volume_label.move(int(1200 * self.mod), int(305 * self.mod))  # Установка позиции метки
        self.volume_label.resize(int(30 * self.mod), int(20 * self.mod))  # Установка размера метки
        self.volume_label.setStyleSheet("QLabel{font-size:" + str(int(17 * self.mod)) + "pt;}")  # Установка стиля метки

        # Кнопка выхода
        self.exit_button = QPushButton("Выход", self)  # Кнопка для выхода из приложения
        self.exit_button.move(int(1170 * self.mod), int(980 * self.mod))  # Установка позиции кнопки
        self.exit_button.resize(int(70 * self.mod), int(100 * self.mod))  # Установка размера кнопки
        self.exit_button.clicked.connect(self.exit_application)  # Подключение сигнала нажатия к методу выхода
        self.exit_button.setStyleSheet("QPushButton{font-size:" + str(int(12 * self.mod)) + "pt;}")  # Установка стиля кнопки

        # QLabel для вывода ошибок
        self.error_label = QLabel(self)  # Метка для отображения сообщений об ошибках
        self.error_label.setStyleSheet("QLabel{font-size:" + str(int(13 * self.mod )) + "pt; color: red;}")  # Установка стиля метки для ошибок
        self.error_label.setGeometry(int(815 * self.mod), int(517 * self.mod), int(400 * self.mod), int(30 * self.mod))  # Установка размеров метки
        self.error_label.setText("")  # Изначально текст метки пустой

        # Процент громкости
        self.volume = QLabel(self)  # Метка для отображения текущего уровня громкости
        self.volume.setText('100%')  # Установка текста метки на 100%
        self.volume.move(int(1189 * self.mod), int(750 * self.mod))  # Установка позиции метки
        self.volume.resize(int(33 * self.mod), int(12 * self.mod))  # Установка размера метки
        self.volume.setStyleSheet("QLabel{font-size:" + str(int(10 * self.mod)) + "pt;}")  # Установка стиля метки

        self.is_playing = 1  # Установка состояния воспроизведения

        self.show()  # Отображение окна

    def play_pause_audio(self):  # Метод для воспроизведения или паузы аудио
        if hasattr(self, 'combined_audio') and self.combined_audio:  # Проверка, существует ли комбинированный аудиофайл
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:  # Создание временного файла
                temp_file_path = temp_file.name  # Получение пути к временно созданному файлу
                # Экспортируем комбинированный аудиофайл во временный файл
                self.combineded_audio = self.combined_audio + self.volume_slid  # Применение громкости
                self.combineded_audio.export(temp_file_path, format="wav")  # Экспорт в формат wav

            pygame.mixer.music.load(temp_file_path)  # Загрузка временного файла в Pygame
            pygame.mixer.music.play()  # Воспроизведение аудио

            os.remove(temp_file_path)  # Удаление временного файла

    def stop_audio(self):  # Метод для остановки воспроизведения
        pygame.mixer.music.stop()  # Остановка воспроизведения

    def closeEvent(self, event):  # Метод для обработки события закрытия окна
        pygame.mixer.music.stop()  # Остановка музыки при закрытии приложения
        event.accept()  # Принятие события

    def show_error_message(self, message):  # Метод для отображения сообщений об ошибках
        self.error_label.setText(message)  # Установка текста ошибки
        QtCore.QTimer.singleShot(2000, lambda: self.error_label.setText(""))  # Скрыть сообщение через 2 секунды

    def set_volume(self):  # Метод для установки громкости
        self.volume_slid = self.volume_slider.value()  # Получение значения громкости от ползунка
        volume = self.volume_slider.value()  # Получаем значение громкости от 0 до 100
        # Устанавливаем иконку громкости
        if volume >= 5:  # Если громкость больше или равна 5
            self.volume_label.setText('🔊')  # Устанавливаем значок громкости
        elif volume < 5 and volume > -10:  # Если громкость меньше 5 и больше -10
            self.volume_label.setText('🔈')  # Устанавливаем значок средней громкости
        else:  # Если громкость меньше или равна -10
            self.volume_label.setText('🔇')  # Устанавливаем значок без звука

        self.volume.setText(str(volume * 100 // 10 + 100) + '%')  # Обновление текста метки громкости

    def exit_application(self):  # Метод для выхода из приложения
        reply = QMessageBox.question(self, 'Выход', 'Вы уверены, что хотите выйти?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)  # Запрос подтверждения выхода
        if reply == QMessageBox.Yes:  # Если пользователь подтвердил выход
            self.close()  # Закрытие приложения

    def show_help(self):  # Метод для отображения окна справки
        help_window = QtWidgets.QDialog(self)  # Создание нового окна
        help_window.setWindowTitle("Справка")  # Заголовок окна
        help_window.setGeometry(200, 200, 600, 400)  # Установка размеров окна

        # Создаем текстовое поле для описания
        help_text = QtWidgets.QTextEdit(help_window)  # Поле для отображения текста справки
        help_text.setGeometry(20, 20, 560, 320)  # Установка размеров текстового поля
        help_text.setReadOnly(True)  # Установка поля как только для чтения

        # Описание функций
        description = """
        Описание функций программы:

        1. Добавить файл
        - Функция: Импортирует аудиофайл в программу.
        - Описание: Позволяет пользователю выбрать аудиофайл с компьютера (поддерживаются форматы .mp3, .wav, .ogg, .flac). После импорта файл становится доступным для дальнейшей работы в программе.

        2. Экспортировать файл
        - Функция: Сохраняет собранный аудиофайл на компьютере.
        - Описание: Позволяет пользователю сохранить текущую аудиодорожку в выбранном формате и в указанном месте на компьютере.

        3. Добавить файл в конец аудиодорожки
        - Функция: Добавляет выбранный аудиофайл в конец текущей аудиодорожки.
        - Описание: Позволяет пользователю выбрать файл из списка и добавить его в конец уже существующей аудиодорожки. Это также обновляет визуализацию аудиодорожки.

        4. Удалить последний файл с аудиодорожки
        - Функция: Удаляет последний добавленный аудиофайл из текущей аудиодорожки.
        - Описание: Если в аудиодорожке есть файлы, пользователь может удалить последний добавленный файл, что также обновляет визуализацию.

        5. Разделить выбранный файл
        - Функция: Разделяет выбранный аудиофайл на две части в указанной точке.
        - Описание: Позволяет пользователю указать время разделения (в секундах) с помощью ползунка. После разделения создаются два новых файла, которые добавляются в проект.

        6. Играть/Остановить
        - Функция: Проигрывает или останавливает воспроизведение текущей аудиодорожки.
        - Описание: Кнопка "Играть" запускает воспроизведение собранной аудиодорожки, в то время как кнопка "Остановить" завершает воспроизведение. Во время воспроизведения программа может быть временно недоступна для взаимодействия.

        7. Ползунок громкости
        - Функция: Изменяет громкость воспроизводимого аудиофайла.
        - Описание: Ползунок позволяет пользователю регулировать громкость аудиодорожки от -10 до +10 (где 0 соответствует 100% громкости). Изменение громкости влияет на все аудиофайлы в проекте.

        8. Визуализация
        - Функция: Отображает графическую визуализацию аудиодорожки.
        - Описание: Визуализация включает два графика: верхний показывает форму волны аудиодорожки, а нижний отображает расположение сегментов в таймлайне. Это помогает пользователю лучше понять структуру аудиодорожки.

        9. История действий
        - Функция: Открывает окно с историей действий пользователя.
        - Описание: Позволяет пользователю просмотреть список всех действий, выполненных в программе, включая импорт, экспорт и изменения в аудиодорожке.

        10. Справка
        - Функция: Открывает окно с описанием всех функций программы.
        - Описание: Предоставляет пользователю подробную информацию о каждой функции программы, включая инструкции и описание возможностей.

        11. Выход
        - Функция: Закрывает приложение.
        - Описание: Позволяет пользователю выйти из программы, при этом перед закрытием будет предложено подтверждение.

        Дополнительные функции:

        - Проверка формата файла при импорте
        - Функция: Проверяет, что загружаемый файл является аудиофайлом.
        - Описание: При попытке импорта файла программа проверяет его формат. Если формат не поддерживается, отображается сообщение об ошибке.

        - Вывод сообщений об ошибках
        - Функция: Отображает сообщения об ошибках пользователю.
        - Описание: В случае возникновения ошибок (например, при попытке загрузить непод ходящий файл) программа выводит сообщение об ошибке, которое исчезает через 2 секунды.
        """

        help_text.setText(description)  # Установка текста справки в текстовое поле

        # Кнопка закрытия
        close_button = QPushButton("Закрыть", help_window)  # Кнопка для закрытия окна справки
        close_button.setGeometry(250, 350, 100, 30)  # Установка размеров кнопки
        close_button.clicked.connect(help_window.close)  # Подключение сигнала нажатия к методу закрытия окна

        help_window.exec_()  # Отображение окна справки

    def _create_output_directory(self):  # Метод для создания выходной директории
        if not os.path.exists(SAVED_FILES_DIR):  # Проверка, существует ли директория
            os.makedirs(SAVED_FILES_DIR)  # Создание директории

    def _create_saved_files_directory(self):  # Метод для создания директории для сохраненных файлов
        if not os.path.exists(SAVED_FILES_DIR):  # Проверка, существует ли директория
            os.makedirs(SAVED_FILES_DIR)  # Создание директории

    def _clean_output_directory(self):  # Метод для очистки выходной директории
        for filename in os.listdir(SAVED_FILES_DIR):  # Перебор всех файлов в директории
            file_path = os.path.join(SAVED_FILES_DIR, filename)  # Получение полного пути к файлу
            try:
                if os.path.isfile(file_path):  # Проверка, является ли путь файлом
                    os.unlink(file_path)  # Удаление файла
            except Exception as e:  # Обработка исключений
                print(f'Error deleting file {file_path}. Reason: {e}')  # Вывод сообщения об ошибке

    def import_files(self):  # Метод для импорта аудиофайлов
        file_path = QtWidgets.QFileDialog.getOpenFileName()[0]  # Открытие диалога выбора файла
        if file_path.endswith(('.mp3', '.wav', '.ogg', '.flac')):  # Проверка на допустимые форматы
            try:
                shutil.copy(file_path, SAVED_FILES_DIR)  # Копирование файла в директорию сохранения
                item = QtWidgets.QListWidgetItem(file_path.split('/')[-1])  # Создание элемента списка
                item.setFont(font)  # Установка шрифта для элемента
                self.items.append(item)  # Добавление элемента в список
                self.list_files.addItem(item)  # Добавление элемента в виджет списка
                self.list_files.setCurrentItem(item)  # Установка текущего элемента
                self.audio_id[file_path.split('/')[-1]] = len(self.audio_files) + 1  # Присвоение ID аудиофайлу
                self.audio_files[len(self.audio_files) + 1] = file_path  # Сохранение пути к аудиофайлу
                self.on_item_clicked(item)  # Обработка нажатия на элемент
            except FileNotFoundError:  # Обработка исключения, если файл не найден
                pass
            self.console_update('Импорт файла: ' + file_path.split('/')[-1])  # Обновление консоли
        else:
            self.console_update('Ошибка: Пожалуйста, выберите звуковой файл (например, .mp3, .wav, .ogg, .flac).')  # Сообщение об ошибке
            self.show_error_message("Ошибка типа")  # Показ сообщения об ошибке

    def add_file_to_end(self):  # Метод для добавления файла в конец аудиодорожки
        if self.used_ID in self.audio_files:  # Проверка, существует ли ID
            audio_to_add = AudioSegment.from_file(self.audio_files[self.used_ID])  # Загрузка аудиофайла
            start = len(self.combined_audio) if hasattr(self, 'combined_audio') else 0  # Определение начала
            end = start + len(audio_to_add)  # Определение конца
            self.audio_segments.append({  # Добавление сегмента в список
                'start': start,
                'end': end,
                'name': os.path.basename(self.audio_files[self.used_ID])  # Имя файла
            })
            self.audio_lengths.append(len(audio_to_add))  # Добавление длины аудиофайла
            if hasattr(self, 'combined_audio'):  # Проверка, существует ли комбинированный аудиофайл
                self.combined_audio += audio_to_add  # Объединение аудиофай ла
            else:
                self.combined_audio = audio_to_add  # Установка комбинированного аудиофайла
            self.console_update(f"Файл {self.audio_files[self.used_ID].split('/')[-1]} добавлен в конец аудио-дорожки.")  # Обновление консоли
            self.visualize_audio()  # Визуализация аудиодорожки
        else:
            self.show_error_message("Ошибка ID")  # Показ сообщения об ошибке
            self.console_update("Недействительный ID файла.")  # Обновление консоли

    def remove_last_file(self):  # Метод для удаления последнего файла из аудиодорожки
        if hasattr(self, 'combined_audio') and self.combined_audio:  # Проверка, существует ли комбинированный аудиофайл
            if self.audio_lengths:  # Проверка, есть ли длины аудиофайлов
                last_length = self.audio_lengths.pop()  # Удаление последней длины
                self.combined_audio = self.combined_audio[:-last_length]  # Удаление последнего сегмента из комбинированного аудиофайла
                self.audio_segments.pop(-1)  # Удаление последнего сегмента
                self.console_update("Последний файл удален.")  # Обновление консоли
                self.visualize_audio()  # Визуализация аудиодорожки
            else:
                self.show_error_message("Ошибка пустой дорожки")  # Показ сообщения об ошибке
                self.console_update("Нет файлов для удаления.")  # Обновление консоли
        else:
            self.console_update("Нет файлов для удаления.")  # Обновление консоли
            self.show_error_message("Ошибка пустой дорожки")  # Показ сообщения об ошибке

    def split_file(self):  # Метод для разделения выбранного аудиофайла
        # Проверяем, существует ли ID выбранного файла в словаре audio_files
        if self.used_ID not in self.audio_files:
            self.show_error_message("Ошибка ID")  # Показ сообщения об ошибке
            self.console_update("Недействительный ID файла.")  # Обновление консоли
            return  # Выход из метода, если ID недействителен

        # Проверяем, существует ли комбинированная аудиодорожка
        if not hasattr(self, 'combined_audio') or self.combined_audio is None:
            self.show_error_message("Ошибка пустой дорожки")  # Показ сообщения об ошибке
            self.console_update("Нет комбинированной аудиодорожки для разделения.")  # Обновление консоли
            return  # Выход из метода, если дорожка отсутствует

        # Загружаем аудиофайл с помощью pydub
        audio = AudioSegment.from_file(self.audio_files[self.used_ID])

        # Получаем время разделения в миллисекундах из ползунка
        split_time_ms = self.split_slider.value() * 1000

        # Разделяем аудиофайл на две части
        part1 = audio[:split_time_ms]  # Первая часть до указанного времени
        part2 = audio[split_time_ms:]  # Вторая часть после указанного времени

        # Генерируем временные метки для имен файлов
        import time
        timestamp = int(time.time())  # Получаем текущее время в секундах
        part1_name = f"part1_{timestamp}_{self.used_name}"  # Имя первой части
        part2_name = f"part2_{timestamp}_{self.used_name}"  # Имя второй части

        # Определяем пути для сохранения разделенных файлов
        part1_path = os.path.join(SAVED_FILES_DIR, part1_name)
        part2_path = os.path.join(SAVED_FILES_DIR, part2_name)

        # Экспортируем каждую часть в формате mp3
        part1.export(part1_path, format="mp3")
        part2.export(part2_path, format="mp3")

        # Создаем новые ID для разделенных файлов
        new_id1 = len(self.audio_files) + 1
        new_id2 = len(self.audio_files) + 2

        # Добавляем новые файлы в словарь audio_files
        self.audio_files[new_id1] = part1_path
        self.audio_files[new_id2] = part2_path

        # Добавляем новые файлы в словарь audio_id
        self.audio_id[part1_name] = new_id1
        self.audio_id[part2_name] = new_id2

        # Добавляем новые файлы в список QListWidget
        self.list_files.addItem(part1_name)
        self.list_files.addItem(part2_name)

        # Обновляем консоль с информацией о разделении файла
        self.console_update(f"Файл {self.used_name} разделен на две части и добавлен в проект")

    def visualize_audio(self):  # Метод для визуализации аудиодорожки
        if hasattr (self, 'combined_audio'):  # Проверка, существует ли комбинированный аудиофайл
            data = np.array(self.combined_audio.get_array_of_samples())  # Получение данных аудиофайла в виде массива

            # Создание фигуры и подграфиков с темно-серым фоном
            fig, ax = plt.subplots(2, 1, figsize=(11.20 * self.mod, 5 * self.mod), facecolor='#1c1c1c')

            # Установка светло-серого фона для осей
            for a in ax:
                a.set_facecolor('#333333')

            # График временной шкалы формы волны
            ax[0].tick_params(axis='x', colors='white')  # Установка цвета меток по оси X
            ax[0].plot(data)  # Построение графика формы волны
            ax[0].set_title('Horizontal timeline of audio track', color='white')  # Заголовок графика
            ax[0].set_xlabel('Time (samples)', color='white')  # Подпись оси X
            ax[0].set_yticks([])  # Скрытие меток по оси Y для ясности
            ax[0].grid(True)  # Включение сетки

            # Горизонтальная столбчатая диаграмма для сегментов аудио
            colors = list(mcolors.TABLEAU_COLORS.values())  # Получение цветов для графиков
            for i, segment in enumerate(self.audio_segments):  # Перебор сегментов аудио
                color = colors[i % len(colors)]  # Выбор цвета для сегмента
                ax[1].barh(0, segment['end'] - segment['start'], left=segment['start'], height=0.1,
                           color=color, label=f"Звук {self.audio_id[segment['name']]}")  # Построение горизонтального столбца
            ax[1].tick_params(axis='x', colors='white')  # Установка цвета меток по оси X
            ax[1].set_title('Audio track segments', color='white')  # Заголовок графика
            ax[1].set_xlabel('Time (samples)', color='white')  # Подпись оси X
            ax[1].set_yticks([])  # Скрытие меток по оси Y
            ax[1].set_ylim(-0.2, 0.2)  # Установка пределов по оси Y
            ax[1].legend(bbox_to_anchor=(0, -0.3), loc='upper left', ncol=4, facecolor='gray')  # Легенда графика

            plt.tight_layout()  # Автоматическая настройка расположения графиков
            output_image_path = os.path.join(SAVED_FILES_DIR, 'audio_visualization.png')  # Путь для сохранения изображения
            plt.savefig(output_image_path)  # Сохранение графика как изображения
            pixmap = QtGui.QPixmap('saved_audio_files/audio_visualization.png')  # Загрузка изображения
            self.graph_label.setScaledContents(True)  # Установка масштабирования содержимого
            self.graph_label.setPixmap(pixmap)  # Установка загруженного изображения в метку

    def export_final_file(self):  # Метод для экспорта финального аудиофайла
        if hasattr(self, 'combined_audio'):  # Проверка, существует ли комбинированный аудиофайл
            # Определяем домашний каталог в зависимости от операционной системы
            if os.name == 'nt':  # для Windows
                default_path = os.path.expanduser('~\\')  # Путь к домашнему каталогу
            else:  # для Linux и MacOS
                default_path = os.path.expanduser('~/')  # Путь к домашнему каталогу

            # Открываем диалог выбора директории
            export_path = QtWidgets.QFileDialog.getSaveFileName(
                self,
                'Сохранить файл',
                default_path,  # используем определенный выше путь
                'Audio Files (*.mp3)'  # Формат для сохранения
            )[0]

            if export_path:  # Если путь был выбран
                try:
                    self.combined_audio += self.volume_slid  # Применение громкости
                    self.combined_audio.export(export_path, format="mp3")  # Экспорт в формат mp3
                    self.console_update(f"Файл успешно экспортирован как {export_path}")  # Обновление консоли ```python
                except Exception as e:  # Обработка исключений
                    self.console_update(f"Ошибка при экспорте файла: {str(e)}")  # Вывод сообщения об ошибке
            else:
                self.console_update("Экспорт отменён")  # Сообщение об отмене экспорта
        else:
            self.show_error_message("Ошибка пустой дорожки")  # Показ сообщения об ошибке
            self.console_update("Нет комбинированной аудиодорожки для экспорта.")  # Обновление консоли

    def truncate_filename(self, filename, max_length):  # Метод для обрезки имени файла
        # Разделяем имя файла и расширение
        name, ext = os.path.splitext(filename)  # Получение имени и расширения файла

        if len(name) > max_length:  # Проверка длины имени файла
            return f"{name[:max_length]}...{ext}"  # Возвращаем обрезанное имя
        return filename  # Возвращаем оригинальное имя

    def console_update(self, txt):  # Метод для обновления консоли
        # Сохраняем сообщение в историю
        self.history.append(txt)  # Добавление сообщения в историю

    def show_history(self):  # Метод для показа истории действий
        history_window = HistoryWindow(self)  # Создание окна истории
        history_window.history_text.setText("\n".join(self.history))  # Установка текста истории
        history_window.exec_()  # Отображение окна истории

    def on_item_clicked(self, item):  # Метод для обработки нажатия на элемент списка
        self.used_name = item.text()  # Получение имени выбранного элемента
        self.used_ID = self.audio_id[self.used_name]  # Получение ID выбранного элемента
        display_name = self.truncate_filename(self.used_name, 20)  # Обрезка имени для отображения
        self.file_inf.setText(f'ID: {self.used_ID}      Name: {display_name}')  # Обновление информации о файле

if __name__ == "__main__":  # Проверка, является ли файл основным
    app = QtWidgets.QApplication([])  # Создание приложения
    app.setPalette(DarkPalette())  # Установка темной палитры
    editor = AudioEditor()  # Создание экземпляра редактора аудио

    app.exec_()  # Запуск приложения
