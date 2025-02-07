import os
import sqlite3
import subprocess
import zipfile
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, QLineEdit, QLabel, QProgressBar, QComboBox)
from PySide6.QtCore import QThread, Signal


# Database Helper
class Database:
    DB_NAME = "settings.db"

    @staticmethod
    def init_db():
        conn = sqlite3.connect(Database.DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS url_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
            """
        )
        conn.commit()

        # Thêm URL nếu chưa có
        cursor.execute("SELECT COUNT(*) FROM url_settings")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO url_settings (url) VALUES (?)",
                [
                    ("https://e-linkpower.hcm.s3storage.vn/videos/khoa-hoc",),
                    ("https://e-linkpower-dev.hcm.s3storage.vn/videos/khoa-hoc",),
                ],
            )
            conn.commit()
        conn.close()

    @staticmethod
    def get_urls():
        conn = sqlite3.connect(Database.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM url_settings")
        urls = [row[0] for row in cursor.fetchall()]
        conn.close()
        return urls


class FFmpegWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)

    def __init__(self, video_path, lesson_id, video_name, base_url):
        super().__init__()
        self.video_path = video_path
        self.lesson_id = lesson_id
        self.video_name = video_name
        self.base_url = base_url

    def run(self):
        try:
            self.progress.emit(10)
            self.generate_enc_key()
            self.create_enc_keyinfo()
            self.progress.emit(30)

            duration_file = self.save_duration()
            self.progress.emit(40)

            output_folder = self.convert_video()
            self.progress.emit(70)

            zip_file, total_files = self.zip_output(output_folder, duration_file)
            self.progress.emit(100)

            self.finished.emit(zip_file)
        except Exception as e:
            self.finished.emit(f"Lỗi: {str(e)}")

    def generate_enc_key(self):
        subprocess.run(["openssl", "rand", "-out", "enc.key", "16"], check=True)

    def create_enc_keyinfo(self):
        key_url = f"{self.base_url}/{self.lesson_id}/{self.video_name}/enc.key"
        with open("enc.keyinfo", "w") as f:
            f.write(f"{key_url}\nenc.key\n")

    def get_video_duration(self):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", self.video_path],
                capture_output=True, text=True, check=True
            )
            return float(result.stdout.strip())
        except Exception as e:
            print(f"Lỗi lấy duration: {e}")
            return None

    def save_duration(self):
        duration = self.get_video_duration()
        if duration is not None:
            with open("duration.txt", "w") as f:
                f.write(str(round(duration, 2)))
            return "duration.txt"
        return None

    def convert_video(self):
        output_folder = os.path.splitext(self.video_path)[0]
        os.makedirs(output_folder, exist_ok=True)

        m3u8_filename = os.path.join(output_folder, f"{self.video_name}.m3u8")
        ts_filename = os.path.join(output_folder, f"{self.video_name}_%03d.ts")

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", self.video_path, "-hls_time", "9",
            "-hls_key_info_file", "enc.keyinfo", "-hls_playlist_type", "vod",
            "-hls_segment_filename", ts_filename, m3u8_filename
        ]

        subprocess.run(ffmpeg_cmd, check=True)
        return output_folder

    def zip_output(self, output_folder, duration_file):
        zip_filename = f"{output_folder}.zip"
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            files = []
            for root, _, filenames in os.walk(output_folder):
                for file in filenames:
                    files.append(os.path.join(root, file))
                    zipf.write(os.path.join(root, file), arcname=file)

            zipf.write("enc.key", arcname="enc.key")
            zipf.write("enc.keyinfo", arcname="enc.keyinfo")
            if duration_file:
                zipf.write("duration.txt", arcname="duration.txt")

            return zip_filename, len(files) + 3


class HLSConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HLS Video Converter")
        self.setGeometry(100, 100, 500, 300)

        self.layout = QVBoxLayout()

        self.lesson_id_label = QLabel("Nhập Lesson ID:")
        self.layout.addWidget(self.lesson_id_label)

        self.lesson_id_input = QLineEdit()
        self.layout.addWidget(self.lesson_id_input)

        self.url_label = QLabel("Chọn Base URL:")
        self.layout.addWidget(self.url_label)

        self.url_selector = QComboBox()
        self.layout.addWidget(self.url_selector)
        self.load_urls()

        self.choose_file_button = QPushButton("Chọn Video & Convert")
        self.choose_file_button.clicked.connect(self.process_video)
        self.layout.addWidget(self.choose_file_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)

    def load_urls(self):
        urls = Database.get_urls()
        self.url_selector.addItems(urls)
        if "https://e-linkpower.hcm.s3storage.vn/videos/khoa-hoc" in urls:
            self.url_selector.setCurrentText("https://e-linkpower.hcm.s3storage.vn/videos/khoa-hoc")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def process_video(self):
        video_path, _ = QFileDialog.getOpenFileName(self, "Chọn file video", "", "MP4 Files (*.mp4)")
        if not video_path:
            return

        lesson_id = self.lesson_id_input.text().strip()
        if not lesson_id:
            QMessageBox.warning(self, "Cảnh báo", "Bạn cần nhập Lesson ID!")
            return

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        base_url = self.url_selector.currentText()

        self.worker = FFmpegWorker(video_path, lesson_id, video_name, base_url)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.start()

    def on_conversion_finished(self, result):
        if "Lỗi" in result:
            QMessageBox.critical(self, "Lỗi", result)
        else:
            QMessageBox.information(self, "Hoàn thành", f"Đã tạo file ZIP: {result}")


if __name__ == "__main__":
    Database.init_db()
    app = QApplication([])
    window = HLSConverter()
    window.show()
    app.exec()
