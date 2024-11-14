import os
import shutil
import pydub
from pydub import AudioSegment, playback
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtWidgets

app = QtWidgets.QApplication([])

SAVED_FILES_DIR = "saved_audio_files"

class AudioEditor:
    def __init__(self):
        self.audio_files = {}
        self.audio_lengths = []
        self.audio_segments = []
        self._create_output_directory()
        self._create_saved_files_directory()
        self._clean_output_directory()

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

    def show_audio_files(self):
        print("\n" * 4)
        print("ID\tНазвание файла")
        for idx, filename in self.audio_files.items():
            print(f"{idx}\t{filename}")

    def add_file_to_end(self, file_id):
        if file_id in self.audio_files:
            audio_to_add = AudioSegment.from_file(self.audio_files[file_id])
            start = len(self.combined_audio) if hasattr(self, 'combined_audio') else 0
            end = start + len(audio_to_add)
            self.audio_segments.append({
                'start': start,
                'end': end,
                'name': os.path.basename(self.audio_files[file_id])
            })
            self.audio_lengths.append(len(audio_to_add))
            if hasattr(self, 'combined_audio'):
                self.combined_audio += audio_to_add
            else:
                self.combined_audio = audio_to_add
            print(f"Файл {self.audio_files[file_id]} добавлен в конец аудио-дорожки.")
        else:
            print("Недействительный ID файла.")

    def remove_last_file(self):
        if hasattr(self, 'combined_audio') and self.combined_audio:
            if self.audio_lengths:
                last_length = self.audio_lengths.pop()
                self.audio_segments.pop(-1)
                self.combined_audio = self.combined_audio[:-last_length]
                print("Последний файл удален.")
            else:
                print("Нет аудиофайлов для удаления.")
        else:
            print("Нет комбинированной аудиодорожки для удаления.")

    def split_file(self, file_id, split_time):
        if file_id in self.audio_files:
            audio = AudioSegment.from_file(self.audio_files[file_id])
            split_time_ms = split_time * 1000
            part1 = audio[:split_time_ms]
            part2 = audio[split_time_ms:]
            part1_path = os.path.join(SAVED_FILES_DIR, f"part1_{self.audio_files[file_id].split('/')[-1]}")
            part2_path = os.path.join(SAVED_FILES_DIR, f"part2_{self.audio_files[file_id].split('/')[-1]}")
            part1.export(part1_path, format="mp3")
            part2.export(part2_path, format="mp3")
            self.audio_files[len(self.audio_files) + 1] = part1_path
            self.audio_files[len(self.audio_files) + 1] = part2_path
            print(f"Файл {self.audio_files[file_id]} разделен на две части.")
        else:
            print("Недействительный ID файла.")

    # def visualize_audio(self):
    #     if hasattr(self, 'combined_audio'):
    #         data = np.array(self.combined_audio.get_array_of_samples())
    #         plt = self.figure.add_subplot(212)
    #         plt.figure(figsize=(12, 3))
    #         plt.plot(data)
    #         plt.set_title('Горизонтальный таймлайн аудиодорожки')
    #         plt.set_xlabel('Время (сэмплы)')
    #         plt.set_yticks([])
    #         plt.grid(True)
    #
    #         colors = list(mcolors.TABLEAU_COLORS.values())
    #         for i, segment in enumerate(self.audio_segments):
    #             color = colors[i % len(colors)]
    #             ax.barh(0, segment['end'] - segment['start'], left=segment['start'], height=0.25,
    #                     color=color, label=f"File {i + 1}: {segment['name']}")
    #         ax.set_title('Сегменты аудиодорожки')
    #         ax.set_xlabel('Время (сэмплы)')
    #         ax.set_yticks([])
    #         ax.set_ylim(-0.2, 0.2)
    #         ax.legend(bbox_to_anchor=(0, -0.3), loc='upper left', ncol=2)
    #         self.canvas.draw()
    #     else:
    #         print("Нет комбинированной аудиодорожки для визуализации.")
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
            # ax[0].plot(data)  # Устанавливаем цвет линии
            ax[0].set_title('Горизонтальный таймлайн аудиодорожки', color='white')
            ax[0].set_xlabel('Время (сэмплы)', color='white')
            ax[0].set_yticks([])  # Скрыть метки по оси Y для ясности
            ax[0].grid(True)  # Устанавливаем цвет сетки

            # Горизонтальная столбчатая диаграмма для сегментов аудиодорожки
            colors = list(mcolors.TABLEAU_COLORS.values())
            # for i, segment in enumerate(self.audio_segments):
            #     color = colors[i % len(colors)]
            #     ax[1].barh(0, segment['end'] - segment['start'], left=segment['start'], height=0.1,
            #                color=color, label=f"File {i + 1}: {segment['name']}")
            ax[1].tick_params(axis='x', colors='white')
            ax[1].set_title('Сегменты аудиодорожки', color='white')
            ax[1].set_xlabel('Время (сэмплы)', color='white')
            ax[1].set_yticks([])  # Скрыть метки по оси Y
            ax[1].set_ylim(-0.2, 0.2)  # Установить пределы по оси Y
            ax[1].legend(bbox_to_anchor=(0, -0.3), loc='upper left', ncol=2, facecolor='gray')

            plt.tight_layout()

            # Сохранение графика в папку saved_audio_files
            output_image_path = os.path.join(SAVED_FILES_DIR, 'audio_visualization.png')
            plt.savefig(output_image_path)
            print(f"График сохранен как {output_image_path}")
            plt.savefig("audio_visualization.png")
            plt.show()
        else:
            print("Нет комбинированной аудиодорожки для визуализации.")

    def play_audio(self):
        # Проигрываем комбинированную аудиодорожку
        if hasattr(self, 'combined_audio'):
            playback.play(self.combined_audio)
        else:
            print("Нет комбинированной аудиодорожки.")

    def export_final_file(self, filename="final_output.mp3"):
        if hasattr(self, 'combined_audio'):
            output_file_path = os.path.join(SAVED_FILES_DIR, filename)
            self.combined_audio.export(output_file_path, format="mp3")
            print(f"Файл экспортирован как {output_file_path}.")
        else:
            print("Нет комбинированной аудиодорожки для экспорта.")

def main():
    editor = AudioEditor()

    while True:
        print("\\n" * 4)
        print("Выберите действие:")
        print("1. Импортировать аудиофайлы")
        print("2. Показать аудиофайлы")
        print("3. Добавить аудиофайл в конец дорожки")
        print("4. Удалить последний аудиофайл")
        print("5. Разделить файл на 2 части")
        print("6. Визуализировать аудиодорожку")
        print("7. Экспортировать конечный файл")
        print("8. Проиграть конечный файл")
        print("9. Выход")

        choice = input("Введите номер действия: ")

        if choice == "1":
            editor.import_files()
        elif choice == "2":
            editor.show_audio_files()
        elif choice == "3":
            file_id = int(input("Введите ID файла для добавления: "))
            editor.add_file_to_end(file_id)
        elif choice == "4":
            editor.remove_last_file()
        elif choice == "5":
            file_id = int(input("Введите ID файла для разделения: "))
            split_time = int(input("Введите секунду для разделения: "))
            editor.split_file(file_id, split_time)
        elif choice == "6":
            editor.visualize_audio()
        elif choice == "7":
            filename = input("Введите имя для экспортируемого файла (по умолчанию final_output.mp3): ")
            if not filename:
                filename = "final_output.mp3"
            editor.export_final_file(filename)
        elif choice == "8":
            editor.play_audio()
        else:
            print("Недействительный выбор, попробуйте снова.")

if __name__ == "__main__":
    main()
