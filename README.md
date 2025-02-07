# Link Power E Learning Video convert tools

## Yêu cầu môi trường

> Lưu ý: Hiện tại hướng dẫn chỉ áp dụng cho Windows, để sử dụng trên các nền tảng khác yêu cầu tự nghiên cứu cách thức build riêng.

- Python 3
- PySide6
- `ffmpeg` được cài đặt trên máy tính với thiết lập mặc định và đã thêm file binary vào `PATH`
  (https://github.com/BtbN/FFmpeg-Builds/releases).
- `openssl` được cài đặt trên máy tính với thiết lập mặc định và đã thêm file binary vào `PATH` (https://slproweb.com/products/Win32OpenSSL.html).
- `pyinstaller` được cài đặt.

## Đóng gói phần mềm

Tại mỗi folder của 1 tool tương ứng (`convert-video-lesson` hoặc `convert-video-tvc`), chạy lệnh sau:

```
pyinstaller --onefile --windowed main.py
```
