import os
import sys
import subprocess
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QVBoxLayout, QMessageBox, QProgressDialog
from PySide6.QtCore import QThread, Signal, QTimer, Qt  # Thêm Qt vào đây

class ConversionThread(QThread):
    progress = Signal(int)
    completed = Signal(str)
    error = Signal(str)

    def __init__(self, input_file, output_file):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file

    def run(self):
        try:
            process = subprocess.Popen(
                ["ffmpeg", "-i", self.input_file, "-c:v", "libx264", "-c:a", "aac",
                 "-hls_time", "10", "-hls_list_size", "0", "-threads", "2", self.output_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            
            for i in range(50):
                self.progress.emit(i)
                self.msleep(100)

            process.communicate()

            if process.returncode == 0:
                self.progress.emit(100)
                self.completed.emit(self.output_file)
            else:
                self.error.emit("Quá trình chuyển đổi thất bại.")
        except Exception as e:
            self.error.emit(str(e))


class VideoConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chuyển đổi MP4 sang M3U8")
        self.setGeometry(300, 300, 400, 200)

        self.layout = QVBoxLayout()
        
        self.label = QLabel("Chọn file MP4:")
        self.layout.addWidget(self.label)
        
        self.input_path = QLineEdit(self)
        self.layout.addWidget(self.input_path)
        
        self.browse_button = QPushButton("Duyệt...", self)
        self.browse_button.clicked.connect(self.browse_file)
        self.layout.addWidget(self.browse_button)
        
        self.convert_button = QPushButton("Chuyển đổi", self)
        self.convert_button.clicked.connect(self.start_conversion)
        self.layout.addWidget(self.convert_button)
        
        self.setLayout(self.layout)

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Chọn file MP4", "", "MP4 files (*.mp4)")
        if file_name:
            self.input_path.setText(file_name)

    def start_conversion(self):
        input_file = self.input_path.text()
        if not input_file:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn file MP4 để chuyển đổi.")
            return

        output_file = os.path.splitext(input_file)[0] + '.m3u8'

        self.progress_dialog = QProgressDialog("Đang chuyển đổi...", "Hủy", 0, 100, self)
        self.progress_dialog.setWindowTitle("Tiến trình chuyển đổi")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)

        self.conversion_thread = ConversionThread(input_file, output_file)
        self.conversion_thread.progress.connect(self.progress_dialog.setValue)
        self.conversion_thread.completed.connect(self.on_conversion_completed)
        self.conversion_thread.error.connect(self.on_conversion_error)
        self.conversion_thread.start()

    def on_conversion_completed(self, output_file):
        self.progress_dialog.close()

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Thành công")
        msg_box.setText(f"Chuyển đổi thành công: {output_file}")
        
        open_folder_button = QPushButton("Mở thư mục")
        open_folder_button.clicked.connect(lambda: self.open_folder(output_file))
        msg_box.addButton(open_folder_button, QMessageBox.ActionRole)
        
        msg_box.exec()

    def on_conversion_error(self, error_message):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Lỗi", f"Lỗi trong quá trình chuyển đổi: {error_message}")

    def open_folder(self, output_file):
        folder_path = os.path.dirname(output_file)
        if sys.platform == "win32":
            os.startfile(folder_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder_path])
        else:
            subprocess.Popen(["xdg-open", folder_path])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoConverterApp()
    window.show()
    sys.exit(app.exec())
