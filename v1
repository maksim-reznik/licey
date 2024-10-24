import os
import shutil
import pydub
from pydub import AudioSegment, playback
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtWidgets

app = QtWidgets.QApplication([])

SAVED_FILES_DIR = "saved_audio_files"

class AudioEditor:
    def __init__(self):
        self.audio_files = {}
        self.audio_lengths = []
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

    def visualize_audio(self):
        if hasattr(self, 'combined_audio'):
            data = np.array(self.combined_audio.get_array_of_samples())
            plt.figure(figsize=(12, 3))


            # Horizontal timeline
            plt.subplot(1, 1, 1)
            plt.plot(data)
            plt.title('Горизонтальный таймлайн аудиодорожки')
            plt.xlabel('Время (сэмплы)')
            plt.yticks([])  # Hide y-axis ticks for clarity
            plt.grid(True)

            plt.tight_layout()
            plt.show()
        else:
            print("Нет комбинированной аудиодорожки для визуализации.")

    def play_audio(self):
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
            break
        else:
            print("Недействительный выбор, попробуйте снова.")

if __name__ == "__main__":
    main()
